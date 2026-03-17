"""Flexible slot management – add slot_status enum, status + date columns to appointment_slots.

Revision ID: g701hi2f9e56
Revises: f601gh1e8d45
Create Date: 2026-03-17 00:00:00.000000

Changes:
- New Postgres enum type ``slot_status`` (available, booked, cancelled, blocked)
- New column ``appointment_slots.status`` (slot_status, NOT NULL, default 'available')
- New column ``appointment_slots.date``   (DATE, nullable, denormalised calendar date)
- New index  ``ix_slots_date`` on ``appointment_slots.date``
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g701hi2f9e56"
down_revision: Union[str, None] = "f601gh1e8d45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Enum values must match app/models/appointment.py  SlotStatus exactly
# ---------------------------------------------------------------------------
SLOT_STATUS_ENUM_NAME = "slot_status"
SLOT_STATUS_VALUES = ("available", "booked", "cancelled", "blocked")


def upgrade() -> None:
    # 1. Create the Postgres enum type
    slot_status_enum = sa.Enum(
        *SLOT_STATUS_VALUES,
        name=SLOT_STATUS_ENUM_NAME,
        create_type=False,   # we create it explicitly below
    )
    op.execute(
        f"CREATE TYPE {SLOT_STATUS_ENUM_NAME} AS ENUM "
        f"({', '.join(repr(v) for v in SLOT_STATUS_VALUES)})"
    )

    # 2. Add the status column (nullable first, then set default + NOT NULL)
    op.add_column(
        "appointment_slots",
        sa.Column(
            "status",
            slot_status_enum,
            nullable=True,
        ),
    )
    # Back-fill existing rows
    op.execute("UPDATE appointment_slots SET status = 'available' WHERE status IS NULL")
    # Now enforce NOT NULL with a server default
    op.alter_column(
        "appointment_slots",
        "status",
        nullable=False,
        server_default="available",
    )

    # 3. Add the denormalised date column (nullable – back-fill from start_time)
    op.add_column(
        "appointment_slots",
        sa.Column("date", sa.Date(), nullable=True),
    )
    op.execute("UPDATE appointment_slots SET date = start_time::date WHERE date IS NULL")

    # 4. Index on date for fast calendar queries
    op.create_index("ix_slots_date", "appointment_slots", ["date"])


def downgrade() -> None:
    op.drop_index("ix_slots_date", table_name="appointment_slots")
    op.drop_column("appointment_slots", "date")
    op.drop_column("appointment_slots", "status")
    op.execute(f"DROP TYPE IF EXISTS {SLOT_STATUS_ENUM_NAME}")
