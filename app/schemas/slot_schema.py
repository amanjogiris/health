"""Appointment slot schemas."""
from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.appointment import SlotStatus


class SlotCreate(BaseModel):
    doctor_id: int
    clinic_id: int
    start_time: datetime.datetime
    end_time: datetime.datetime
    capacity: int = Field(1, ge=1, le=10)
    status: SlotStatus = SlotStatus.AVAILABLE

    @model_validator(mode="after")
    def validate_times(self) -> "SlotCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        return self


class SlotUpdate(BaseModel):
    """Partial update for an existing slot.

    All fields are optional. Pass ``force=True`` in the query string to allow
    editing a slot that has been booked (admin override).
    """

    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    capacity: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[SlotStatus] = None

    @model_validator(mode="after")
    def validate_times(self) -> "SlotUpdate":
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        return self


class SlotResponse(BaseModel):
    id: int
    doctor_id: int
    clinic_id: int
    date: Optional[datetime.date] = None
    start_time: datetime.datetime
    end_time: datetime.datetime
    status: SlotStatus = SlotStatus.AVAILABLE
    is_booked: bool
    capacity: int
    booked_count: int
    is_active: bool
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class SlotToggleResponse(BaseModel):
    """Response after toggling a slot's is_active flag."""

    id: int
    is_active: bool
    message: str


class SlotGenerateRange(BaseModel):
    """Request body for date-range slot generation."""

    date_from: datetime.date = Field(..., description="Start date (inclusive)")
    date_to: datetime.date = Field(..., description="End date (exclusive)")
    duration_minutes: Optional[int] = Field(
        None, ge=5, le=480, description="Override the doctor's default consultation duration"
    )

    @model_validator(mode="after")
    def validate_range(self) -> "SlotGenerateRange":
        if self.date_to <= self.date_from:
            raise ValueError("date_to must be after date_from.")
        if (self.date_to - self.date_from).days > 365:
            raise ValueError("Range cannot exceed 365 days.")
        return self
