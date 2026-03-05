"""Doctor schemas."""
from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AvailabilityInput(BaseModel):
    """One day-of-week + time window supplied by the admin."""
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday … 6=Sunday")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", examples=["09:00"])
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", examples=["17:00"])


class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    day_of_week: int
    start_time: str
    end_time: str

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def coerce_time(cls, v: object) -> str:
        if isinstance(v, datetime.time):
            return v.strftime("%H:%M")
        return str(v)


class DoctorCreate(BaseModel):
    user_id: int
    clinic_id: int
    specialty: str = Field(..., min_length=1, max_length=100)
    license_number: str = Field(..., min_length=1, max_length=50)
    qualifications: Optional[str] = None
    experience_years: int = Field(0, ge=0, le=80)
    max_patients_per_day: int = Field(10, ge=1, le=100)
    consultation_duration_minutes: int = Field(15, ge=5, le=120)


class DoctorRegister(BaseModel):
    """Combined user + doctor creation; admin/super_admin only."""
    # User fields
    name: str = Field(..., min_length=1, max_length=150)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6)
    mobile_no: Optional[str] = Field(None, max_length=20)
    # Doctor profile fields
    clinic_id: int
    specialty: str = Field(..., min_length=1, max_length=100)
    license_number: str = Field(..., min_length=1, max_length=50)
    qualifications: Optional[str] = None
    experience_years: int = Field(0, ge=0, le=80)
    max_patients_per_day: int = Field(10, ge=1, le=100)
    consultation_duration_minutes: int = Field(15, ge=5, le=120)
    # Optional availability to set immediately
    availability: Optional[List[AvailabilityInput]] = None


class DoctorUpdate(BaseModel):
    clinic_id: Optional[int] = None
    specialty: Optional[str] = Field(None, max_length=100)
    qualifications: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0, le=80)
    max_patients_per_day: Optional[int] = Field(None, ge=1, le=100)
    consultation_duration_minutes: Optional[int] = Field(None, ge=5, le=120)


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    clinic_id: int
    specialty: str
    license_number: str
    qualifications: Optional[str] = None
    experience_years: int
    max_patients_per_day: int
    consultation_duration_minutes: int = 15
    is_active: bool
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    # Enriched fields (populated by service layer JOIN)
    doctor_name: Optional[str] = None
    clinic_name: Optional[str] = None
    # Availability (populated on request)
    availability: Optional[List[AvailabilityResponse]] = None
