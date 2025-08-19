"""add policy columns and versioning to tenant_settings

Revision ID: 20250819_03_policy_columns
Revises: 20250819_02_action_approvals
Create Date: 2025-08-19
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250819_03_policy_columns"
down_revision = "20250819_02_action_approvals"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tenant_settings") as batch:
        batch.add_column(sa.Column("auto_approve_enabled", sa.Boolean(), server_default=sa.text("1")))
        batch.add_column(sa.Column("risk_threshold_default", sa.Float(), server_default=sa.text("0.80")))
        batch.add_column(sa.Column("action_whitelist", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
        batch.add_column(sa.Column("action_blacklist", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
        batch.add_column(sa.Column("data", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
        batch.add_column(sa.Column("version", sa.Integer(), server_default=sa.text("1")))
        batch.add_column(sa.Column("updated_by_id", sa.String(64), nullable=True))
        batch.alter_column("enabled_domains", existing_type=sa.JSON(), server_default=sa.text("'{}'"), nullable=False)
        batch.alter_column("feature_flags", existing_type=sa.JSON(), server_default=sa.text("'{}'"), nullable=False)


def downgrade():
    with op.batch_alter_table("tenant_settings") as batch:
        batch.alter_column("feature_flags", server_default=None, nullable=True)
        batch.alter_column("enabled_domains", server_default=None, nullable=True)
        batch.drop_column("updated_by_id")
        batch.drop_column("version")
        batch.drop_column("data")
        batch.drop_column("action_blacklist")
        batch.drop_column("action_whitelist")
        batch.drop_column("risk_threshold_default")
        batch.drop_column("auto_approve_enabled")
