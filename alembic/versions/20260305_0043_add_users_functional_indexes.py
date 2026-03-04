"""Add functional indexes on users table to fix seq_scans.

Revision ID: 0043
Revises: 0042
Create Date: 2026-03-05

pg_stat_user_tables showed 2.5M seq_scans and 21B rows read on users table.
Root causes:
  1. LOWER(username) queries bypass the plain idx_users_username index
  2. raw_data JSONB lookups (id/userId/user_id) have no indexes
  3. LOWER(email) LIKE queries bypass idx_users_email

Uses CONCURRENTLY (via autocommit) to avoid table locks on production.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0043'
down_revision: Union[str, None] = '0042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execution_options(isolation_level="AUTOCOMMIT")

    # 1. Функциональный индекс для LOWER(username)
    #    WHERE LOWER(username) = LOWER($1) / WHERE LOWER(username) = ANY(...)
    conn.execute(op.inline_literal("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_lower
        ON users (LOWER(username))
    """))

    # 2. Функциональный индекс для LOWER(email)
    conn.execute(op.inline_literal("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_lower
        ON users (LOWER(email))
        WHERE email IS NOT NULL
    """))

    # 3. raw_data->>'id' — числовой ID из Remnawave Panel
    conn.execute(op.inline_literal("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_raw_data_id
        ON users ((raw_data->>'id'))
        WHERE raw_data IS NOT NULL
    """))

    # 4. raw_data->>'userId' — альтернативное поле ID
    conn.execute(op.inline_literal("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_raw_data_userId
        ON users ((raw_data->>'userId'))
        WHERE raw_data IS NOT NULL
    """))

    # 5. raw_data->>'user_id' — альтернативное поле ID
    conn.execute(op.inline_literal("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_raw_data_user_id
        ON users ((raw_data->>'user_id'))
        WHERE raw_data IS NOT NULL
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execution_options(isolation_level="AUTOCOMMIT")

    conn.execute(op.inline_literal("DROP INDEX CONCURRENTLY IF EXISTS idx_users_username_lower"))
    conn.execute(op.inline_literal("DROP INDEX CONCURRENTLY IF EXISTS idx_users_email_lower"))
    conn.execute(op.inline_literal("DROP INDEX CONCURRENTLY IF EXISTS idx_users_raw_data_id"))
    conn.execute(op.inline_literal("DROP INDEX CONCURRENTLY IF EXISTS idx_users_raw_data_userId"))
    conn.execute(op.inline_literal("DROP INDEX CONCURRENTLY IF EXISTS idx_users_raw_data_user_id"))
