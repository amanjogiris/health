"""Appointment schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AppointmentBook(BaseModel):
    patient_id: int
    doctor_id: int
    slot_id: int
    clinic_id: int
    reason_for_visit: Optional[str] = Field(None, max_length=500)


class AppointmentCancel(BaseModel):
    cancelled_reason: str = Field(..., min_length=1, max_length=500)


class AppointmentNotesUpdate(BaseModel):
    """Payload for a doctor to update prescription / notes on an appointment."""
    notes: str = Field(..., min_length=0, max_length=5000)


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    clinic_id: int
    slot_id: int
    status: str
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Enriched join fields (populated by service layer)
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None
    slot_time: Optional[str] = None

    @field_validator("status", mode="before")
    @classmethod
    def normalise_status(cls, v: object) -> str:
        """Return the *value* string for enum members; lowercase otherwise.

        The DB stores UPPERCASE enum labels ('BOOKED', 'CANCELLED', …).
        SQLAlchemy maps these to the Python ``AppointmentStatus`` enum member
        whose .value is lowercase ('booked', 'cancelled', …).
        We always expose the lowercase .value so the frontend status-config
        lookup works consistently.
        """
        if hasattr(v, "value"):
            return str(v.value).lower()
        return str(v).lower()

    class Config:
        from_attributes = True


class BookingResponse(BaseModel):
    """Uniform envelope returned by the /book endpoint."""
    success: bool
    message: str
    appointment_id: Optional[int] = None
    appointment: Optional[AppointmentResponse] = None
