"""add parent_asset_id column to file_assets

Revision ID: 2b1a0d3f7c8d
Revises: 1f2e3d4c5b6a
Create Date: 2025-08-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2b1a0d3f7c8d"
down_revision = "1f2e3d4c5b6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "file_assets", sa.Column("parent_asset_id", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("file_assets", "parent_asset_id")

