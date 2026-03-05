"""normalise_user_roles_to_lowercase

Revision ID: d401ef9c6b23
Revises: c301de8f5a12
Create Date: 2026-03-06 00:01:00.000000

Renames the existing uppercase enum values (ADMIN, DOCTOR, PATIENT)
to their lowercase counterparts so they match the Python UserRole.value
strings used by the model with values_callable.

Note: SUPER_ADMIN was already added as 'super_admin' (lowercase) in
the previous migration, so it needs no change.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "d401ef9c6b23"
down_revision: Union[str, Sequence[str], None] = "c301de8f5a12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE … RENAME VALUE requires PostgreSQL 10+.
    # These run outside a transaction implicitly because the enum type
    # change does not require one in Postgres 10+.
    op.execute("ALTER TYPE user_roles RENAME VALUE 'ADMIN' TO 'admin'")
    op.execute("ALTER TYPE user_roles RENAME VALUE 'DOCTOR' TO 'doctor'")
    op.execute("ALTER TYPE user_roles RENAME VALUE 'PATIENT' TO 'patient'")
    # 'super_admin' is already lowercase — nothing to do.
    # Add 'SUPER_ADMIN' uppercase alias is NOT needed; the model value is 'super_admin'.


def downgrade() -> None:
    op.execute("ALTER TYPE user_roles RENAME VALUE 'admin' TO 'ADMIN'")
    op.execute("ALTER TYPE user_roles RENAME VALUE 'doctor' TO 'DOCTOR'")
    op.execute("ALTER TYPE user_roles RENAME VALUE 'patient' TO 'PATIENT'")
