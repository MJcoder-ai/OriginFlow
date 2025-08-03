"""Add sub_elements column to component_master

Revision ID: add_sub_elements_column
Revises: add_ports_dependencies_layer
Create Date: 2025-08-30

This migration adds a ``sub_elements`` JSON column to the
``component_master`` table.  The column stores nested
sub-components or accessories that belong to a master component.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_sub_elements_column'
down_revision: Union[str, Sequence[str], None] = 'add_ports_dependencies_layer'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ``sub_elements`` JSON column to component_master."""
    with op.batch_alter_table("component_master") as batch_op:
        batch_op.add_column(sa.Column("sub_elements", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove ``sub_elements`` column from component_master."""
    with op.batch_alter_table("component_master") as batch_op:
        batch_op.drop_column("sub_elements")

