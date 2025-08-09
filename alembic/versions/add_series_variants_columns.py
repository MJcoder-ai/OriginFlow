"""Add series_name and variants columns to component_master

Revision ID: add_series_variants_columns
Revises: 2b1a0d3f7c8d
Create Date: 2025-06-02

This migration adds two optional columns to the ``component_master`` table:
``series_name`` for the product family identifier and ``variants`` for an array
of per-product attributes extracted from multi-option datasheets.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_series_variants_columns'
down_revision: Union[str, Sequence[str], None] = '2b1a0d3f7c8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ``series_name`` and ``variants`` columns."""
    with op.batch_alter_table('component_master') as batch_op:
        batch_op.add_column(sa.Column('series_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('variants', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove ``series_name`` and ``variants`` columns."""
    with op.batch_alter_table('component_master') as batch_op:
        batch_op.drop_column('variants')
        batch_op.drop_column('series_name')
