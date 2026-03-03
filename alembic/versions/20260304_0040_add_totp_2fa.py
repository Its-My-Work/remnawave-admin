"""Add TOTP 2FA columns to admin_accounts.

Revision ID: 0040
Revises: 0039
Create Date: 2026-03-04

Adds columns for TOTP two-factor authentication:
- totp_secret: encrypted TOTP secret key
- totp_enabled: whether 2FA is active for this account
- backup_codes: JSON array of one-time backup codes
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0040'
down_revision: Union[str, None] = '0039'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('admin_accounts', sa.Column('totp_secret', sa.String(255), nullable=True))
    op.add_column('admin_accounts', sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('admin_accounts', sa.Column('backup_codes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('admin_accounts', 'backup_codes')
    op.drop_column('admin_accounts', 'totp_enabled')
    op.drop_column('admin_accounts', 'totp_secret')
