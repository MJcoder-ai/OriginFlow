"""add image fields to file_assets

Revision ID: 1f2e3d4c5b6a
Revises: 0560f8aa0021
Create Date: 2025-08-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1f2e3d4c5b6a'
down_revision = '0560f8aa0021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('file_assets', sa.Column('is_extracted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('file_assets', sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('file_assets', sa.Column('width', sa.Integer(), nullable=True))
    op.add_column('file_assets', sa.Column('height', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('file_assets', 'height')
    op.drop_column('file_assets', 'width')
    op.drop_column('file_assets', 'is_primary')
    op.drop_column('file_assets', 'is_extracted')
