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
    # Immutable wrapper for timestamptz cast (needed for functional index)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION immutable_tstz(text)
        RETURNS timestamptz AS $$
            SELECT CASE WHEN $1 IS NOT NULL THEN $1::timestamptz ELSE NULL END;
        $$ LANGUAGE sql IMMUTABLE STRICT
        """
    )
    # Functional index on online_at extracted from JSONB via immutable wrapper
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_online_at "
        "ON users (immutable_tstz(raw_data->'userTraffic'->>'onlineAt')) "
        "WHERE raw_data->'userTraffic'->>'onlineAt' IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_online_at")
    op.execute("DROP FUNCTION IF EXISTS immutable_tstz(text)")
