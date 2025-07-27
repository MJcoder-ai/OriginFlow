"""add component master table

Revision ID: dd4899121b5a
Revises: e8f9c0d1b3a4
Create Date: 2025-07-27 12:36:56.733671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd4899121b5a'
down_revision: Union[str, Sequence[str], None] = 'e8f9c0d1b3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by creating ``component_master`` table."""

    op.create_table(
        "component_master",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("part_number", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("manufacturer", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("voltage", sa.Float(), nullable=True),
        sa.Column("current", sa.Float(), nullable=True),
        sa.Column("power", sa.Float(), nullable=True),
        sa.Column("specs", sa.JSON(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("availability", sa.Integer(), nullable=True),
        sa.Column("deprecated", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_component_master_part_number", "component_master", ["part_number"], unique=True)
    op.create_index("ix_component_master_name", "component_master", ["name"], unique=False)
    op.create_index("ix_component_master_manufacturer", "component_master", ["manufacturer"], unique=False)
    op.create_index("ix_component_master_category", "component_master", ["category"], unique=False)


def downgrade() -> None:
    """Drop ``component_master`` table on downgrade."""

    op.drop_index("ix_component_master_category", table_name="component_master")
    op.drop_index("ix_component_master_manufacturer", table_name="component_master")
    op.drop_index("ix_component_master_name", table_name="component_master")
    op.drop_index("ix_component_master_part_number", table_name="component_master")
    op.drop_table("component_master")
