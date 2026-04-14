"""Add user_node_traffic_history for 24h traffic calculation.

Revision ID: 0057
Revises: 0056
Create Date: 2026-04-14

Stores per-user-per-node traffic deltas computed during each sync
cycle. Enables computing traffic consumed over a rolling 24-hour
window by summing deltas: SUM(delta_bytes) WHERE recorded_at >= NOW() - '24h'.
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0057"
down_revision: Union[str, None] = "0056"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_node_traffic_history (
            id BIGSERIAL PRIMARY KEY,
            user_uuid UUID NOT NULL,
            node_uuid UUID NOT NULL,
            delta_bytes BIGINT NOT NULL DEFAULT 0,
            recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_unt_history_node_recorded
        ON user_node_traffic_history (node_uuid, recorded_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_unt_history_user_node_recorded
        ON user_node_traffic_history (user_uuid, node_uuid, recorded_at DESC)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_node_traffic_history")
