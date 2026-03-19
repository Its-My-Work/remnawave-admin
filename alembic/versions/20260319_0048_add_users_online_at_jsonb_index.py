"""Add functional index on users raw_data->userTraffic->onlineAt for online_filter queries.

Revision ID: 0048
Revises: 0047
Create Date: 2026-03-19
"""
from alembic import op

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Functional index for online_at filtering (stored in JSONB)
    # Partial index: only rows where onlineAt is not null
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_online_at "
        "ON users (((raw_data->'userTraffic'->>'onlineAt')::timestamptz)) "
        "WHERE raw_data->'userTraffic'->>'onlineAt' IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_online_at")
