"""Add REJECTED value to appointment_status enum.

Revision ID: e501fg0d7c34
Revises: c303dd4e5b12
Create Date: 2025-01-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e501fg0d7c34"
down_revision: Union[str, None] = "c303dd4e5b12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'REJECTED'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    pass
