"""add needs_manual_name_review flag to file_assets

Revision ID: f1a2b3c4d5e6
Revises: dd4899121b5a
Create Date: 2025-09-05 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'dd4899121b5a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'file_assets',
        sa.Column(
            'needs_manual_name_review',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
    )


def downgrade() -> None:
    op.drop_column('file_assets', 'needs_manual_name_review')
