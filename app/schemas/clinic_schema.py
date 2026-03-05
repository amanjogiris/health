"""Clinic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ClinicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1)
    phone: str = Field(..., max_length=20)
    email: Optional[EmailStr] = None
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., max_length=10)


class ClinicUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=10)


class ClinicResponse(BaseModel):
    id: int
    name: str
    address: str
    phone: str
    email: Optional[str] = None
    city: str
    state: str
    zip_code: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
