"""agent persistence: catalog, versions, tenant state

Revision ID: 20250819_01_agents_persistence
Revises: f1a2b3c4d5e6
Create Date: 2025-08-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20250819_01_agents_persistence"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_catalog",
        sa.Column("name", sa.String(length=100), primary_key=True),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("domain", sa.String(length=64), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("risk_class", sa.String(length=32), nullable=True),
        sa.Column("capabilities", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "agent_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("agent_name", sa.String(length=100), sa.ForeignKey("agent_catalog.name")),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("spec", sa.JSON(), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("validation_report", sa.JSON(), nullable=True),
        sa.Column("created_by_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("agent_name", "version", name="uq_agent_versions_name_version"),
    )
    op.create_index("ix_agent_versions_agent_status", "agent_versions", ["agent_name", "status"])

    op.create_table(
        "tenant_agent_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("agent_name", sa.String(length=100), sa.ForeignKey("agent_catalog.name")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("pinned_version", sa.Integer(), nullable=True),
        sa.Column("config_override", sa.JSON(), nullable=True),
        sa.Column("updated_by_id", sa.String(length=36), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("tenant_id", "agent_name", name="uq_tenant_agent_state_tenant_agent"),
    )
    op.create_index("ix_tenant_agent_state_tenant_agent", "tenant_agent_state", ["tenant_id", "agent_name"])


def downgrade() -> None:
    op.drop_index("ix_tenant_agent_state_tenant_agent", table_name="tenant_agent_state")
    op.drop_table("tenant_agent_state")
    op.drop_index("ix_agent_versions_agent_status", table_name="agent_versions")
    op.drop_table("agent_versions")
    op.drop_table("agent_catalog")

