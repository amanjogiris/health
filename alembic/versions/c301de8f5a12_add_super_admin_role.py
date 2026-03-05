"""add_super_admin_role

Revision ID: c301de8f5a12
Revises: b102cc3f4a01
Create Date: 2026-03-06 00:00:00.000000

Adds the 'super_admin' value to the PostgreSQL enum type 'user_roles'.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c301de8f5a12"
down_revision: Union[str, Sequence[str], None] = "b102cc3f4a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE … ADD VALUE outside a transaction
    op.execute("ALTER TYPE user_roles ADD VALUE IF NOT EXISTS 'super_admin'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # A full recreate would be needed; for safety we leave it as a no-op.
    pass
