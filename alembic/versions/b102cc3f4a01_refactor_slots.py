"""refactor_slots_start_end_time

Revision ID: b102cc3f4a01
Revises: a421bffd3c9f
Create Date: 2026-03-05 00:00:00.000000

Migrates appointment_slots from (slot_datetime, duration_minutes) to
(start_time, end_time) to reflect the layered-architecture model.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b102cc3f4a01"
down_revision: Union[str, Sequence[str], None] = "a421bffd3c9f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column(
        "appointment_slots",
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointment_slots",
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
    )

    # Populate from existing data (end_time = slot_datetime + duration_minutes)
    op.execute(
        """
        UPDATE appointment_slots
        SET start_time = slot_datetime,
            end_time   = slot_datetime + MAKE_INTERVAL(mins => duration_minutes)
        """
    )

    # Make non-nullable now that data is populated
    op.alter_column("appointment_slots", "start_time", nullable=False)
    op.alter_column("appointment_slots", "end_time", nullable=False)

    # Create new index, drop old ones
    op.create_index("ix_slots_start_time", "appointment_slots", ["start_time"])

    op.drop_index("ix_slots_slot_datetime", table_name="appointment_slots")
    op.drop_index(
        op.f("ix_appointment_slots_slot_datetime"), table_name="appointment_slots"
    )

    # Remove old columns
    op.drop_column("appointment_slots", "slot_datetime")
    op.drop_column("appointment_slots", "duration_minutes")


def downgrade() -> None:
    op.add_column(
        "appointment_slots",
        sa.Column("slot_datetime", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "appointment_slots",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE appointment_slots
        SET slot_datetime    = start_time,
            duration_minutes = EXTRACT(EPOCH FROM (end_time - start_time))::INT / 60
        """
    )

    op.alter_column("appointment_slots", "slot_datetime", nullable=False)
    op.alter_column("appointment_slots", "duration_minutes", nullable=False)

    op.create_index(
        "ix_slots_slot_datetime", "appointment_slots", ["slot_datetime"]
    )
    op.drop_index("ix_slots_start_time", table_name="appointment_slots")
    op.drop_column("appointment_slots", "start_time")
    op.drop_column("appointment_slots", "end_time")
