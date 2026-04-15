"""Webhook security hardening + retry queue + descriptions.

Revision ID: 0059
Revises: 0058
Create Date: 2026-04-16

Adds:
- webhook_subscriptions.signature_version (v1 legacy, v2 with timestamp)
- webhook_subscriptions.consecutive_failures (for auto-disable)
- webhook_subscriptions.auto_disabled_at + disabled_reason
- webhook_subscriptions.description
- api_keys.description
- webhook_retry_queue table for background delivery retries
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0059"
down_revision: Union[str, None] = "0058"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE webhook_subscriptions ADD COLUMN IF NOT EXISTS signature_version VARCHAR(8) NOT NULL DEFAULT 'v1'")
    op.execute("ALTER TABLE webhook_subscriptions ADD COLUMN IF NOT EXISTS consecutive_failures INT NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE webhook_subscriptions ADD COLUMN IF NOT EXISTS auto_disabled_at TIMESTAMPTZ")
    op.execute("ALTER TABLE webhook_subscriptions ADD COLUMN IF NOT EXISTS disabled_reason TEXT")
    op.execute("ALTER TABLE webhook_subscriptions ADD COLUMN IF NOT EXISTS description TEXT")

    op.execute("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS description TEXT")

    op.execute("""
        CREATE TABLE IF NOT EXISTS webhook_retry_queue (
            id BIGSERIAL PRIMARY KEY,
            webhook_id INTEGER NOT NULL REFERENCES webhook_subscriptions(id) ON DELETE CASCADE,
            event TEXT NOT NULL,
            payload JSONB NOT NULL,
            attempt INT NOT NULL DEFAULT 1,
            max_attempts INT NOT NULL DEFAULT 3,
            next_try_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhook_retry_next
        ON webhook_retry_queue (next_try_at) WHERE next_try_at IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS webhook_retry_queue")
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS description")
    op.execute("ALTER TABLE webhook_subscriptions DROP COLUMN IF EXISTS description")
    op.execute("ALTER TABLE webhook_subscriptions DROP COLUMN IF EXISTS disabled_reason")
    op.execute("ALTER TABLE webhook_subscriptions DROP COLUMN IF EXISTS auto_disabled_at")
    op.execute("ALTER TABLE webhook_subscriptions DROP COLUMN IF EXISTS consecutive_failures")
    op.execute("ALTER TABLE webhook_subscriptions DROP COLUMN IF EXISTS signature_version")
