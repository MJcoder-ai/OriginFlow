"""add tenant settings and pending actions tables

Revision ID: 123456789abc
Revises: f1a2b3c4d5e6
Create Date: 2024-08-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "123456789abc"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_settings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("ai_auto_approve", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("risk_threshold_low", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("risk_threshold_medium", sa.Float, nullable=False, server_default="0.75"),
        sa.Column("risk_threshold_high", sa.Float, nullable=False, server_default="1.1"),
        sa.Column("whitelisted_actions", sa.JSON, nullable=True),
        sa.Column("enabled_domains", sa.JSON, nullable=True),
        sa.Column("feature_flags", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_tenant_settings_tenant_id", "tenant_settings", ["tenant_id"])

    op.create_table(
        "pending_actions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("project_id", sa.String(length=64), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("agent_name", sa.String(length=100), nullable=False),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("risk_class", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("decided_by", sa.String(length=100), nullable=True),
        sa.Column("decision_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime, nullable=True),
    )
    op.create_index(
        "ix_pending_actions_tenant_status_created",
        "pending_actions",
        ["tenant_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_pending_actions_tenant_status_created", table_name="pending_actions")
    op.drop_table("pending_actions")
    op.drop_index("ix_tenant_settings_tenant_id", table_name="tenant_settings")
    op.drop_table("tenant_settings")

