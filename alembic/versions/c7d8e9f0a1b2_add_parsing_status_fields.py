"""Add parsing status fields to file_assets

Revision ID: c7d8e9f0a1b2
Revises: 0560f8aa0021
Create Date: 2025-07-20 09:00:00.000000Z
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b2'
down_revision = '0560f8aa0021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('file_assets', sa.Column('parsing_status', sa.String(), nullable=True))
    op.add_column('file_assets', sa.Column('parsing_error', sa.Text(), nullable=True))
    op.add_column('file_assets', sa.Column('is_human_verified', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('file_assets', 'is_human_verified')
    op.drop_column('file_assets', 'parsing_error')
    op.drop_column('file_assets', 'parsing_status')
