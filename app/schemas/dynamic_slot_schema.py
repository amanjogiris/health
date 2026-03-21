"""Pydantic schemas for the dynamic (factory-driven) slot & booking flow."""
from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.dynamic_appointment import DynamicAppointmentStatus


# ── Slot schemas ───────────────────────────────────────────────────────────────

class DynamicSlotResponse(BaseModel):
    """A single factory-generated time slot returned to the client.

    The slot is *never* persisted in the database; it is computed on the fly
    from the doctor's availability + existing bookings.
    """

    start_time: datetime.datetime
    end_time: datetime.datetime
    is_available: bool
    duration_minutes: int

    @classmethod
    def from_dynamic_slot(cls, slot) -> "DynamicSlotResponse":
        """Convert a ``DynamicSlot`` dataclass to a serialisable response."""
        return cls(
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
            duration_minutes=slot.duration_minutes,
        )


class DoctorSlotsResponse(BaseModel):
    """Full response for GET /doctors/{id}/slots?date=..."""

    doctor_id: int
    date: datetime.date
    slot_interval_minutes: int
    total_slots: int
    available_slots: int
    slots: List[DynamicSlotResponse]


# ── Booking schemas ────────────────────────────────────────────────────────────

class DynamicBookRequest(BaseModel):
    """Request body for POST /appointments/dynamic.

    ``slots_requested`` defaults to 1 (single-slot booking).  Set it to N for
    a multi-slot block (the actual booking duration becomes
    ``slot_interval × slots_requested`` minutes).
    """

    doctor_id: int
    patient_id: int
    clinic_id: int
    start_time: datetime.datetime = Field(
        ..., description="Start of the desired slot (must align to the doctor's slot grid)"
    )
    slots_requested: int = Field(
        default=1,
        ge=1,
        le=8,
        description="Number of consecutive slots to book (multi-slot support)",
    )
    reason_for_visit: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def start_must_be_future(self) -> "DynamicBookRequest":
        # Slots are stored as "IST time in UTC field" (e.g. 10:00+00:00 means 10:00 AM IST).
        # To correctly reject past slots we compare against IST now expressed the same way:
        # strip the IST offset from current IST time so it matches the stored fake-UTC convention.
        IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        now_as_fake_utc = datetime.datetime.now(tz=IST).replace(tzinfo=datetime.timezone.utc)
        start = self.start_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=datetime.timezone.utc)
        if start < now_as_fake_utc:
            raise ValueError("start_time must be in the future.")
        return self


class DynamicCancelRequest(BaseModel):
    cancelled_reason: str = Field(..., min_length=1, max_length=500)


class DynamicAppointmentResponse(BaseModel):
    """Response for create / cancel / get operations on dynamic appointments."""

    id: int
    doctor_id: int
    patient_id: int
    clinic_id: int
    start_time: datetime.datetime
    end_time: datetime.datetime
    status: str
    slots_count: int = 1            # how many interval-slots this booking spans
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
    cancelled_at: Optional[datetime.datetime] = None
    cancelled_reason: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    @classmethod
    def from_orm_with_interval(
        cls,
        appt,
        interval_minutes: int,
    ) -> "DynamicAppointmentResponse":
        duration = int(
            (appt.end_time - appt.start_time).total_seconds() / 60
        )
        slots_count = max(1, duration // interval_minutes) if interval_minutes else 1
        status_val = (
            appt.status.value
            if hasattr(appt.status, "value")
            else str(appt.status)
        )
        return cls(
            id=appt.id,
            doctor_id=appt.doctor_id,
            patient_id=appt.patient_id,
            clinic_id=appt.clinic_id,
            start_time=appt.start_time,
            end_time=appt.end_time,
            status=status_val,
            slots_count=slots_count,
            reason_for_visit=appt.reason_for_visit,
            notes=appt.notes,
            cancelled_at=appt.cancelled_at,
            cancelled_reason=appt.cancelled_reason,
            created_at=appt.created_at,
        )

    class Config:
        from_attributes = True


# ── Availability schemas (extended with slot_interval) ─────────────────────────

class AvailabilityInputWithInterval(BaseModel):
    """Availability rule with an explicit slot_interval field."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday … 6=Sunday")
    start_time: datetime.time
    end_time: datetime.time
    slot_interval: int = Field(
        default=15, ge=5, le=120, description="Slot duration in minutes"
    )

    @model_validator(mode="after")
    def validate_window(self) -> "AvailabilityInputWithInterval":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        return self
