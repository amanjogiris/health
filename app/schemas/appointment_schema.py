"""Appointment schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AppointmentBook(BaseModel):
    patient_id: int
    doctor_id: int
    slot_id: int
    clinic_id: int
    reason_for_visit: Optional[str] = Field(None, max_length=500)


class AppointmentCancel(BaseModel):
    cancelled_reason: str = Field(..., min_length=1, max_length=500)


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

    class Config:
        from_attributes = True
