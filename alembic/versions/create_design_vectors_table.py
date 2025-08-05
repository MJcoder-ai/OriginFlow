"""Create design_vectors table

Revision ID: create_design_vectors_table
Revises: add_ai_action_vectors_table
Create Date: 2025-09-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'create_design_vectors_table'
down_revision: Union[str, Sequence[str], None] = 'add_ai_action_vectors_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create design_vectors table."""
    op.create_table(
        "design_vectors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("vector", sa.JSON(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade() -> None:
    """Drop design_vectors table."""
    op.drop_table("design_vectors")
