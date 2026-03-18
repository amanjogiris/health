"""DoctorLeave model – tracks when a doctor is unavailable."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Column, Date, Index, Integer, Text, Time

from app.db.base import Base
from app.models.mixins import TimestampMixin


class DoctorLeave(Base, TimestampMixin):
    """A leave/unavailability block for a doctor.

    Two types:
    - Full-day: ``is_full_day=True``, ``start_time`` and ``end_time`` are NULL.
    - Partial:  ``is_full_day=False``, ``start_time`` and ``end_time`` define
                the window during which the doctor is unavailable.

    These blocks are checked during both slot generation and booking:
    - Slots that overlap a leave window are exposed as ``is_available=False``.
    - Booking attempts into a leave window are rejected with an error.
    """

    __tablename__ = "doctor_leaves"
    __table_args__ = (
        Index("ix_doctor_leaves_doctor_date", "doctor_id", "date"),
    )

    id: int = Column(Integer, primary_key=True)
    doctor_id: int = Column(Integer, nullable=False, index=True)
    date: object = Column(Date, nullable=False)
    is_full_day: bool = Column(Boolean, nullable=False, default=True)
    # Only set when is_full_day=False
    start_time: Optional[object] = Column(Time, nullable=True)
    end_time: Optional[object] = Column(Time, nullable=True)
    reason: Optional[str] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        kind = "full-day" if self.is_full_day else f"{self.start_time}-{self.end_time}"
        return f"<DoctorLeave doctor_id={self.doctor_id} date={self.date} {kind}>"


__all__ = ["DoctorLeave"]
