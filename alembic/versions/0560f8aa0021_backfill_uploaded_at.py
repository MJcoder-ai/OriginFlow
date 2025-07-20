"""backfill uploaded_at for existing file_assets

Revision ID: 0560f8aa0021
Revises: a1b2c3d4e5f6
Create Date: 2025-08-01 00:00:00.000000
"""
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '0560f8aa0021'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect_name = conn.dialect.name

    if dialect_name == "postgresql":
        timestamp_func = "NOW()"
    elif dialect_name == "sqlite":
        timestamp_func = "CURRENT_TIMESTAMP"
    else:
        timestamp_func = "NOW()"

    conn.execute(
        text(
            f"""
            UPDATE file_assets
            SET uploaded_at = {timestamp_func}
            WHERE uploaded_at IS NULL;
            """
        )
    )


def downgrade() -> None:
    # No-op: data update only
    pass
