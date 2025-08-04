"""Create ai_action_vectors table

Revision ID: add_ai_action_vectors_table
Revises: add_sub_elements_column
Create Date: 2025-09-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_ai_action_vectors_table'
down_revision: Union[str, Sequence[str], None] = 'add_sub_elements_column'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ai_action_vectors table."""
    op.create_table(
        "ai_action_vectors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("component_type", sa.String(), nullable=True),
        sa.Column("user_prompt", sa.String(), nullable=False),
        sa.Column("anonymized_prompt", sa.String(), nullable=False),
        sa.Column("design_context", sa.JSON(), nullable=True),
        sa.Column("anonymized_context", sa.JSON(), nullable=True),
        sa.Column("session_history", sa.JSON(), nullable=True),
        sa.Column("approval", sa.Boolean(), nullable=False),
        sa.Column("confidence_shown", sa.Float(), nullable=True),
        sa.Column("confirmed_by", sa.String(), nullable=False, server_default="human"),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Drop ai_action_vectors table."""
    op.drop_table("ai_action_vectors")
