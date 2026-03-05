"""User and authentication schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Public sign-up — only PATIENT accounts may be self-registered."""

    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    mobile_no: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None

    # Always patient; ignored even if sent by client
    @property
    def role(self) -> str:
        return "patient"


class AdminCreate(BaseModel):
    """Schema for SUPER_ADMIN to create ADMIN user accounts."""

    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    mobile_no: Optional[str] = Field(None, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    mobile_no: Optional[str] = None
    address: Optional[str] = None
    is_verified: bool
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str = "Successfully logged out."
