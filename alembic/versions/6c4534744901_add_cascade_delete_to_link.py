"""add cascade delete to link

Revision ID: 6c4534744901
Revises: ce005598b788
Create Date: 2025-07-09 01:25:00.412502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c4534744901'
down_revision: Union[str, Sequence[str], None] = 'ce005598b788'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to cascade delete links when a component is removed."""
    op.drop_index(op.f("ix_links_id"), table_name="links")
    op.drop_table("links")
    op.create_table(
        "links",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column(
            "source_id",
            sa.String(),
            sa.ForeignKey("components.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_id",
            sa.String(),
            sa.ForeignKey("components.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_links_id"), "links", ["id"], unique=False)


def downgrade() -> None:
    """Revert cascade delete behavior."""
    op.drop_index(op.f("ix_links_id"), table_name="links")
    op.drop_table("links")
    op.create_table(
        "links",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["components.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["components.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_links_id"), "links", ["id"], unique=False)
