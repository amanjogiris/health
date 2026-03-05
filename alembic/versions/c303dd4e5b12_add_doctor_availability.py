"""add_doctor_availability_and_consultation_duration

Revision ID: c303dd4e5b12
Revises: b102cc3f4a01
Create Date: 2026-03-06 00:00:00.000000

Adds:
  - doctors.consultation_duration_minutes (default 15)
  - doctor_availability table (weekly availability rules)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c303dd4e5b12"
down_revision: Union[str, Sequence[str], None] = "d401ef9c6b23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add consultation_duration_minutes to doctors
    op.add_column(
        "doctors",
        sa.Column(
            "consultation_duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default="15",
        ),
    )

    # 2. Create doctor_availability table
    op.create_table(
        "doctor_availability",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_doctor_availability_doctor_id",
        "doctor_availability",
        ["doctor_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_doctor_availability_doctor_id", table_name="doctor_availability")
    op.drop_table("doctor_availability")
    op.drop_column("doctors", "consultation_duration_minutes")
