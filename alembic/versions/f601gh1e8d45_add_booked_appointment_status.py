"""Add BOOKED value to appointment_status enum.

Revision ID: f601gh1e8d45
Revises: e501fg0d7c34
Create Date: 2026-03-10 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "f601gh1e8d45"
down_revision: Union[str, None] = "e501fg0d7c34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE appointment_status ADD VALUE IF NOT EXISTS 'BOOKED'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values.
    pass
