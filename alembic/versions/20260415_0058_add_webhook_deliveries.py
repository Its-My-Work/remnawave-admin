"""Add webhook_deliveries table for dispatch history.

Revision ID: 0058
Revises: 0057
Create Date: 2026-04-15

Stores each webhook POST attempt with status, response body, duration, and
error. Used for the "Delivery history" UI and debugging failed endpoints.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0058"
down_revision: Union[str, None] = "0057"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id BIGSERIAL PRIMARY KEY,
            webhook_id INTEGER NOT NULL REFERENCES webhook_subscriptions(id) ON DELETE CASCADE,
            event TEXT NOT NULL,
            status_code INTEGER NOT NULL DEFAULT 0,
            response_body TEXT,
            error TEXT,
            duration_ms INTEGER,
            sent_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook_sent
        ON webhook_deliveries (webhook_id, sent_at DESC)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS webhook_deliveries")
