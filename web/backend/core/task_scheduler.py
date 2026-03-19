"""Background scheduler for cron-based script execution on nodes."""
import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def task_scheduler_loop():
    """Check scheduled_tasks every 60s and execute matching cron entries."""
    await asyncio.sleep(10)  # initial startup delay
    while True:
        try:
            from shared.database import db_service
            if not db_service.is_connected:
                await asyncio.sleep(60)
                continue

            from web.backend.core.automation_engine import cron_matches_now

            async with db_service.acquire() as conn:
                tasks = await conn.fetch(
                    """
                    SELECT st.id, st.script_id, st.node_uuid::text, st.cron_expression,
                           st.env_vars, ns.content AS script_content, ns.name AS script_name,
                           ns.timeout_seconds, ns.requires_root
                    FROM scheduled_tasks st
                    JOIN node_scripts ns ON ns.id = st.script_id
                    WHERE st.is_enabled = true
                    """
                )

            for task in tasks:
                try:
                    if not cron_matches_now(task["cron_expression"]):
                        continue

                    task_id = task["id"]
                    node_uuid = task["node_uuid"]
                    script_name = task["script_name"]

                    logger.info(
                        "Scheduled task %d (%s) triggered for node %s",
                        task_id, script_name, node_uuid,
                    )

                    # Execute script via agent WebSocket
                    try:
                        from web.backend.core.agent_manager import agent_manager
                        from web.backend.core.agent_hmac import sign_command_with_ts

                        agent_token = None
                        async with db_service.acquire() as conn:
                            row = await conn.fetchrow(
                                "SELECT agent_token FROM nodes WHERE uuid = $1", node_uuid
                            )
                            if row:
                                agent_token = row["agent_token"]

                        if not agent_token:
                            logger.warning("No agent token for node %s, skipping task %d", node_uuid, task_id)
                            await _update_task_status(db_service, task_id, "failed")
                            continue

                        env_vars = task["env_vars"]
                        if isinstance(env_vars, str):
                            env_vars = json.loads(env_vars)

                        cmd_payload = {
                            "type": "exec_script",
                            "script": task["script_content"],
                            "timeout": task["timeout_seconds"] or 300,
                            "as_root": task["requires_root"] or False,
                            "env": env_vars or {},
                        }

                        payload_with_ts, sig = sign_command_with_ts(cmd_payload, agent_token)
                        sent = await agent_manager.send_to_node(node_uuid, {
                            "type": "command",
                            "payload": payload_with_ts,
                            "signature": sig,
                        })

                        status = "success" if sent else "failed"
                        if not sent:
                            logger.warning("Agent not connected for node %s, task %d", node_uuid, task_id)

                    except Exception as e:
                        logger.error("Failed to execute scheduled task %d: %s", task_id, e)
                        status = "failed"

                    await _update_task_status(db_service, task_id, status)

                except Exception as e:
                    logger.error("Error processing scheduled task: %s", e)

        except Exception as e:
            logger.error("Task scheduler loop error: %s", e)

        await asyncio.sleep(60)


async def _update_task_status(db_service, task_id: int, status: str):
    """Update task last_run_at, last_status, run_count."""
    try:
        async with db_service.acquire() as conn:
            await conn.execute(
                """
                UPDATE scheduled_tasks
                SET last_run_at = NOW(), last_status = $2,
                    run_count = run_count + 1, updated_at = NOW()
                WHERE id = $1
                """,
                task_id, status,
            )
    except Exception as e:
        logger.error("Failed to update task %d status: %s", task_id, e)
