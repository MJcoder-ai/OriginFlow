"""merge heads

Revision ID: e89a5814189e
Revises: 1f2e3d4c5b6a, create_design_vectors_table
Create Date: 2025-08-07 07:17:00.128267

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'e89a5814189e'
down_revision: Union[
    str, Sequence[str], None
] = ('1f2e3d4c5b6a', 'create_design_vectors_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
