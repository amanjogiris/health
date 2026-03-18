"""Dynamic slot system: add slot_interval to doctor_availability + create dynamic_appointments table.

Revision ID: h801ij3g0f67
Revises: g701hi2f9e56
Create Date: 2026-03-17 00:00:00.000000

Changes:
- ``doctor_availability.slot_interval``  INT NOT NULL DEFAULT 15
- New table ``dynamic_appointments`` with status enum ``dynamic_appointment_status``
- UniqueConstraint (doctor_id, start_time) on ``dynamic_appointments``
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "h801ij3g0f67"
down_revision: Union[str, None] = "g701hi2f9e56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENUM_NAME = "dynamic_appointment_status"
_ENUM_VALUES = ("booked", "cancelled", "completed", "no_show")


def upgrade() -> None:
    # ── 1. Add slot_interval column to doctor_availability ─────────────────
    # Use raw SQL with IF NOT EXISTS to be safe against partial prior runs.
    op.execute(
        "ALTER TABLE doctor_availability "
        "ADD COLUMN IF NOT EXISTS slot_interval INTEGER NOT NULL DEFAULT 15"
    )

    # ── 2. Create dynamic_appointment_status enum (idempotent) ─────────────
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{_ENUM_NAME}') THEN
                CREATE TYPE {_ENUM_NAME} AS ENUM ({', '.join(repr(v) for v in _ENUM_VALUES)});
            END IF;
        END
        $$;
    """)
    dyn_status_enum = postgresql.ENUM(*_ENUM_VALUES, name=_ENUM_NAME, create_type=False)

    # ── 3. Create dynamic_appointments table (idempotent) ──────────────────
    # op.create_table raises if the table already exists; guard with raw SQL.
    op.execute("DROP TABLE IF EXISTS dynamic_appointments")
    op.create_table(
        "dynamic_appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("clinic_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            dyn_status_enum,
            nullable=False,
            server_default="booked",
        ),
        sa.Column("reason_for_visit", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_reason", sa.Text(), nullable=True),
        # SoftDeleteMixin
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        # TimestampMixin
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
            nullable=False,
        ),
        # Constraints
        sa.UniqueConstraint("doctor_id", "start_time", name="uq_dynAppt_doctor_start"),
    )

    # ── 4. Indexes ─────────────────────────────────────────────────────────
    op.create_index("ix_dyn_appt_doctor_id", "dynamic_appointments", ["doctor_id"], if_not_exists=True)
    op.create_index("ix_dyn_appt_patient_id", "dynamic_appointments", ["patient_id"], if_not_exists=True)
    op.create_index("ix_dyn_appt_start_time", "dynamic_appointments", ["start_time"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_dyn_appt_start_time", table_name="dynamic_appointments", if_exists=True)
    op.drop_index("ix_dyn_appt_patient_id", table_name="dynamic_appointments", if_exists=True)
    op.drop_index("ix_dyn_appt_doctor_id", table_name="dynamic_appointments", if_exists=True)
    op.drop_table("dynamic_appointments", if_exists=True)
    op.execute(f"DROP TYPE IF EXISTS {_ENUM_NAME}")
    op.execute("ALTER TABLE doctor_availability DROP COLUMN IF EXISTS slot_interval")
