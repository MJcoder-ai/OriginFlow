"""action approvals v1: pending_actions enhancements

Revision ID: 20250819_02_action_approvals
Revises: 20250819_01_agents_persistence
Create Date: 2025-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20250819_02_action_approvals"
down_revision: Union[str, None] = "20250819_01_agents_persistence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pending_actions", sa.Column("reason", sa.String(length=400), nullable=True))
    op.add_column("pending_actions", sa.Column("requested_by_id", sa.String(length=36), nullable=True))
    op.add_column("pending_actions", sa.Column("approved_by_id", sa.String(length=36), nullable=True))
    op.add_column(
        "pending_actions",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.add_column("pending_actions", sa.Column("applied_at", sa.DateTime(), nullable=True))

    # replace old index with new ones
    op.drop_index("ix_pending_actions_tenant_status_created", table_name="pending_actions")
    op.create_index(
        "ix_pending_actions_tenant_status", "pending_actions", ["tenant_id", "status"]
    )
    op.create_index("ix_pending_actions_session", "pending_actions", ["session_id"])
    op.create_index("ix_pending_actions_created_at", "pending_actions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_pending_actions_created_at", table_name="pending_actions")
    op.drop_index("ix_pending_actions_session", table_name="pending_actions")
    op.drop_index("ix_pending_actions_tenant_status", table_name="pending_actions")
    op.create_index(
        "ix_pending_actions_tenant_status_created",
        "pending_actions",
        ["tenant_id", "status", "created_at"],
    )

    op.drop_column("pending_actions", "applied_at")
    op.drop_column("pending_actions", "updated_at")
    op.drop_column("pending_actions", "approved_by_id")
    op.drop_column("pending_actions", "requested_by_id")
    op.drop_column("pending_actions", "reason")

