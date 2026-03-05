"""Patient schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PatientUpdate(BaseModel):
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

    class Config:
        from_attributes = True
