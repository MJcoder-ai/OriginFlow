"""Add ports, dependencies and layer_affinity columns to component_master

Revision ID: add_ports_dependencies_layer
Revises: f0e1d2c3b4a5
Create Date: 2025-08-30

This migration extends the component_master table with additional
fields to support hierarchical component modelling.  The new
columns capture port definitions, dependency information and
preferred canvas layers for each component.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_ports_dependencies_layer'
down_revision: Union[str, Sequence[str], None] = 'f0e1d2c3b4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new JSON columns for ports, dependencies and layer affinity."""
    with op.batch_alter_table("component_master") as batch_op:
        batch_op.add_column(sa.Column("ports", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("dependencies", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("layer_affinity", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove the added columns on downgrade."""
    with op.batch_alter_table("component_master") as batch_op:
        batch_op.drop_column("layer_affinity")
        batch_op.drop_column("dependencies")
        batch_op.drop_column("ports")
