"""Pydantic schemas for the doctor leave / unavailability system."""
from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class DoctorLeaveCreate(BaseModel):
    """Request body for creating a leave record.

    - Set ``is_full_day=True`` (default) for a full-day block.
    - Set ``is_full_day=False`` and provide ``start_time`` + ``end_time`` for
      a partial-day block.
    """

    date: datetime.date = Field(..., description="Calendar date of the leave")
    is_full_day: bool = Field(True, description="True = block the entire working day")
    start_time: Optional[datetime.time] = Field(
        None, description="Required when is_full_day=False"
    )
    end_time: Optional[datetime.time] = Field(
        None, description="Required when is_full_day=False"
    )
    reason: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_partial(self) -> "DoctorLeaveCreate":
        if not self.is_full_day:
            if self.start_time is None or self.end_time is None:
                raise ValueError(
                    "start_time and end_time are required for a partial-day leave."
                )
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time.")
        return self


class DoctorLeaveResponse(BaseModel):
    """Leave record returned from the API."""

    id: int
    doctor_id: int
    date: datetime.date
    is_full_day: bool
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    reason: Optional[str] = None
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


__all__ = ["DoctorLeaveCreate", "DoctorLeaveResponse"]
