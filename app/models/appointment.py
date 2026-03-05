"""Appointment-related models for the health_app."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Index, Integer, Text

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class AppointmentStatus(enum.Enum):
    """Status of an appointment."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class AppointmentSlot(Base, TimestampMixin, SoftDeleteMixin):
    """Appointment slot model for doctor availability."""

    __tablename__ = "appointment_slots"
    __table_args__ = (
        Index("ix_slots_doctor_id", "doctor_id"),
        Index("ix_slots_clinic_id", "clinic_id"),
        Index("ix_slots_start_time", "start_time"),
    )

    id: int = Column(Integer, primary_key=True)
    doctor_id: int = Column(Integer, nullable=False, index=True)
    clinic_id: int = Column(Integer, nullable=False, index=True)
    start_time: datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time: datetime = Column(DateTime(timezone=True), nullable=False)
    is_booked: bool = Column(Boolean, default=False, nullable=False)
    capacity: int = Column(Integer, default=1, nullable=False)
    booked_count: int = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<AppointmentSlot id={self.id} doctor_id={self.doctor_id} start_time={self.start_time}>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "clinic_id": self.clinic_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "is_booked": self.is_booked,
            "capacity": self.capacity,
            "booked_count": self.booked_count,
            "available_slots": self.capacity - self.booked_count,
        }


class Appointment(Base, TimestampMixin, SoftDeleteMixin):
    """Appointment booking model."""

    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_patient_id", "patient_id"),
        Index("ix_appointments_doctor_id", "doctor_id"),
        Index("ix_appointments_slot_id", "slot_id"),
    )

    id: int = Column(Integer, primary_key=True)
    patient_id: int = Column(Integer, nullable=False, index=True)
    doctor_id: int = Column(Integer, nullable=False, index=True)
    clinic_id: int = Column(Integer, nullable=False)
    slot_id: int = Column(Integer, nullable=False, unique=True, index=True)
    status: AppointmentStatus = Column(
        SAEnum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.PENDING,
    )
    reason_for_visit: Optional[str] = Column(Text, nullable=True)
    notes: Optional[str] = Column(Text, nullable=True)
    cancelled_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Optional[str] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} patient_id={self.patient_id} doctor_id={self.doctor_id} status={self.status.value}>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "clinic_id": self.clinic_id,
            "slot_id": self.slot_id,
            "status": self.status.value if isinstance(self.status, AppointmentStatus) else str(self.status),
            "reason_for_visit": self.reason_for_visit,
            "notes": self.notes,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancelled_reason": self.cancelled_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


__all__ = ["AppointmentStatus", "AppointmentSlot", "Appointment"]
