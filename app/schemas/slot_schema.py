"""Appointment slot schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SlotCreate(BaseModel):
    doctor_id: int
    clinic_id: int
    start_time: datetime
    end_time: datetime
    capacity: int = Field(1, ge=1, le=10)

    @model_validator(mode="after")
    def validate_times(self) -> "SlotCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        return self


class SlotUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = Field(None, ge=1, le=10)


class SlotResponse(BaseModel):
    id: int
    doctor_id: int
    clinic_id: int
    start_time: datetime
    end_time: datetime
    is_booked: bool
    capacity: int
    booked_count: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
