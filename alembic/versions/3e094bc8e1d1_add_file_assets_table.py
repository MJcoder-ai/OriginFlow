"""Add file_assets table

Revision ID: 3e094bc8e1d1
Revises: 768c7f1c566a
Create Date: 2025-07-14 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '3e094bc8e1d1'
down_revision: Union[str, Sequence[str], None] = '768c7f1c566a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'file_assets',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('mime', sa.String(), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('component_id', sa.String(), sa.ForeignKey('components.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index(op.f('ix_file_assets_id'), 'file_assets', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_file_assets_id'), table_name='file_assets')
    op.drop_table('file_assets')
