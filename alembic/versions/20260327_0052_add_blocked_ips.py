"""Add blocked_ips table for IP-level blocking on nodes.

Revision ID: 0052
Revises: 0051
Create Date: 2026-03-27
"""
from alembic import op

revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS blocked_ips (
            id SERIAL PRIMARY KEY,
            ip_cidr CIDR NOT NULL UNIQUE,
            reason TEXT,
            added_by_admin_id INTEGER,
            added_by_username VARCHAR(255),
            country_code VARCHAR(10),
            asn_org VARCHAR(255),
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX idx_blocked_ips_expires
        ON blocked_ips (expires_at)
        WHERE expires_at IS NOT NULL
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS blocked_ips")
