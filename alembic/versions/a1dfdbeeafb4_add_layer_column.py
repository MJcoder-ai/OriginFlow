"""add layer column

Revision ID: a1dfdbeeafb4
Revises: dd4899121b5a
Create Date: 2025-07-30 15:36:18.697360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1dfdbeeafb4'
down_revision: Union[str, Sequence[str], None] = 'dd4899121b5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ``layer`` column to ``schematic_components``."""
    op.add_column(
        "schematic_components",
        sa.Column(
            "layer",
            sa.String(),
            nullable=True,
            server_default="Single-Line Diagram",
        ),
    )


def downgrade() -> None:
    """Remove ``layer`` column from ``schematic_components``."""
    op.drop_column("schematic_components", "layer")
