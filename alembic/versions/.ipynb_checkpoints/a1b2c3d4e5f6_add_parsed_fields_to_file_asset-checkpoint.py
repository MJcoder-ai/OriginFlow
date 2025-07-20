"""add parsed_payload & parsed_at columns

Revision ID: a1b2c3d4e5f6
Revises: b824b42b81b1
Create Date: 2025-07-19 21:00:00.000000Z
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'b824b42b81b1'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "file_assets",
        sa.Column("parsed_payload", sa.JSON(), nullable=True),
    )
    op.add_column(
        "file_assets",
        sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # --- THIS IS THE MISSING LINE ---
    op.add_column(
        "file_assets",
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
    )

def downgrade() -> None:
    op.drop_column("file_assets", "parsed_at")
    op.drop_column("file_assets", "parsed_payload")
    # --- ALSO ADD THIS FOR COMPLETENESS ---
    op.drop_column("file_assets", "uploaded_at")
