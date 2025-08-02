"""Add AI action log table

Revision ID: f0e1d2c3b4a5
Revises: a1dfdbeeafb4
Create Date: 2025-08-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f0e1d2c3b4a5'
down_revision: Union[str, Sequence[str], None] = 'a1dfdbeeafb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create ai_action_log table"""
    op.create_table(
        "ai_action_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(), nullable=True),
        sa.Column("prompt_text", sa.Text(), nullable=True),
        sa.Column("proposed_action", sa.JSON(), nullable=False),
        sa.Column("user_decision", sa.String(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Drop ai_action_log table"""
    op.drop_table("ai_action_log")
