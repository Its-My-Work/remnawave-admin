"""Add scheduled_tasks table for cron-based script execution.

Revision ID: 0049
Revises: 0048
Create Date: 2026-03-20
"""
from alembic import op

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            id SERIAL PRIMARY KEY,
            script_id INT NOT NULL REFERENCES node_scripts(id) ON DELETE CASCADE,
            node_uuid UUID NOT NULL REFERENCES nodes(uuid) ON DELETE CASCADE,
            cron_expression VARCHAR(100) NOT NULL,
            is_enabled BOOLEAN DEFAULT TRUE,
            env_vars JSONB DEFAULT '{}',
            last_run_at TIMESTAMPTZ,
            last_status VARCHAR(20),
            next_run_at TIMESTAMPTZ,
            run_count INT DEFAULT 0,
            created_by INT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_enabled "
        "ON scheduled_tasks(is_enabled) WHERE is_enabled = true"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_script "
        "ON scheduled_tasks(script_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS scheduled_tasks CASCADE")
