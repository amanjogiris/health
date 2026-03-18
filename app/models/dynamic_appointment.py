"""Dynamic appointment model – used by the factory-driven slot booking flow.

Unlike the legacy ``Appointment`` model (which requires a pre-created
``AppointmentSlot`` row), a ``DynamicAppointment`` stores the booking window
directly (start_time / end_time) and uses a DB-level unique constraint on
(doctor_id, start_time) to prevent double-booking at the database layer.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    Text,
    UniqueConstraint,
)

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class DynamicAppointmentStatus(enum.Enum):
    """Lifecycle status of a dynamic appointment."""

    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class DynamicAppointment(Base, TimestampMixin, SoftDeleteMixin):
    """Appointment booked against a factory-generated (dynamic) slot.

    The booking window is stored directly; no ``AppointmentSlot`` row is
    pre-created.  The unique constraint on (doctor_id, start_time) together
    with the application-level SELECT FOR UPDATE guard prevents any two
    patients from booking the same slot concurrently.
    """

    __tablename__ = "dynamic_appointments"
    __table_args__ = (
        # DB-level guard: same doctor cannot have two bookings at the same start.
        UniqueConstraint("doctor_id", "start_time", name="uq_dynAppt_doctor_start"),
        Index("ix_dyn_appt_doctor_id", "doctor_id"),
        Index("ix_dyn_appt_patient_id", "patient_id"),
        Index("ix_dyn_appt_start_time", "start_time"),
    )

    id: int = Column(Integer, primary_key=True)
    doctor_id: int = Column(Integer, nullable=False, index=True)
    patient_id: int = Column(Integer, nullable=False, index=True)
    clinic_id: int = Column(Integer, nullable=False)
    # The actual booking window (timezone-aware, stored as UTC)
    start_time: datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time: datetime = Column(DateTime(timezone=True), nullable=False)
    status: DynamicAppointmentStatus = Column(
        SAEnum(
            DynamicAppointmentStatus,
            name="dynamic_appointment_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=DynamicAppointmentStatus.BOOKED,
        server_default="booked",
    )
    reason_for_visit: Optional[str] = Column(Text, nullable=True)
    notes: Optional[str] = Column(Text, nullable=True)
    cancelled_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Optional[str] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<DynamicAppointment id={self.id} doctor_id={self.doctor_id} "
            f"patient_id={self.patient_id} start={self.start_time}>"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "clinic_id": self.clinic_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value if self.status else None,
            "reason_for_visit": self.reason_for_visit,
            "notes": self.notes,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancelled_reason": self.cancelled_reason,
        }


__all__ = ["DynamicAppointment", "DynamicAppointmentStatus"]
