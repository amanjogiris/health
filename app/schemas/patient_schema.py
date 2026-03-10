"""Patient schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class PatientUpdate(BaseModel):
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    blood_group: Optional[str] = Field(
        None, pattern=r"^(O\+|O\-|A\+|A\-|B\+|B\-|AB\+|AB\-)$"
    )
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=20)


class AdminPatientUpdate(BaseModel):
    """Full patient update for admin – covers both user-level and patient-profile fields."""
    # User-level fields
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    mobile_no: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    # Patient-profile fields
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    blood_group: Optional[str] = Field(
        None, pattern=r"^(O\+|O\-|A\+|A\-|B\+|B\-|AB\+|AB\-)$"
    )
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=20)


class PatientResponse(BaseModel):
    id: int
    user_id: int
    date_of_birth: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Enriched fields (populated by admin service layer)
    patient_name: Optional[str] = None
    email: Optional[str] = None
    mobile_no: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True
