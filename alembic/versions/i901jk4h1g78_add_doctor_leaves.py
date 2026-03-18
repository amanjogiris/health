"""Add doctor_leaves table.

Revision ID: i901jk4h1g78
Revises: h801ij3g0f67
Create Date: 2026-03-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "i901jk4h1g78"
down_revision: str = "h801ij3g0f67"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "doctor_leaves",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "is_full_day",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        # TimestampMixin columns
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
    )
    op.create_index(
        "ix_doctor_leaves_doctor_date",
        "doctor_leaves",
        ["doctor_id", "date"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_doctor_leaves_doctor_id",
        "doctor_leaves",
        ["doctor_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_doctor_leaves_doctor_id", table_name="doctor_leaves", if_exists=True)
    op.drop_index("ix_doctor_leaves_doctor_date", table_name="doctor_leaves", if_exists=True)
    op.drop_table("doctor_leaves", if_exists=True)
