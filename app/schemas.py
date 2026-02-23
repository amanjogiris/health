"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# User & Auth Schemas
# ============================================================================


class UserBase(BaseModel):
    """Base schema for user information."""

    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    mobile_no: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None


class UserRegister(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field("patient", pattern="^(admin|doctor|patient)$")


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    role: str
    is_verified: bool
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthToken(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================================================
# Patient Schemas
# ============================================================================


class PatientCreate(BaseModel):
    """Schema for creating a patient."""

    user_id: int
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    blood_group: Optional[str] = Field(None, pattern="^(O\\+|O\\-|A\\+|A\\-|B\\+|B\\-|AB\\+|AB\\-)$")
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=20)


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""

    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    blood_group: Optional[str] = Field(None, pattern="^(O\\+|O\\-|A\\+|A\\-|B\\+|B\\-|AB\\+|AB\\-)$")
    allergies: Optional[str] = None
    emergency_contact: Optional[str] = Field(None, max_length=20)


class PatientResponse(PatientCreate):
    """Schema for patient response."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# Clinic Schemas
# ============================================================================


class ClinicCreate(BaseModel):
    """Schema for creating a clinic."""

    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1)
    phone: str = Field(..., max_length=20)
    email: Optional[EmailStr] = None
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    zip_code: str = Field(..., max_length=10)


class ClinicUpdate(BaseModel):
    """Schema for updating a clinic."""

    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=10)


class ClinicResponse(ClinicCreate):
    """Schema for clinic response."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# Doctor Schemas
# ============================================================================


class DoctorCreate(BaseModel):
    """Schema for creating a doctor."""

    user_id: int
    clinic_id: int
    specialty: str = Field(..., min_length=1, max_length=100)
    license_number: str = Field(..., min_length=1, max_length=50)
    qualifications: Optional[str] = None
    experience_years: int = Field(0, ge=0, le=80)
    max_patients_per_day: int = Field(10, ge=1, le=100)


class DoctorUpdate(BaseModel):
    """Schema for updating a doctor."""

    clinic_id: Optional[int] = None
    specialty: Optional[str] = Field(None, max_length=100)
    qualifications: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0, le=80)
    max_patients_per_day: Optional[int] = Field(None, ge=1, le=100)


class DoctorResponse(DoctorCreate):
    """Schema for doctor response."""

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# Appointment Slot Schemas
# ============================================================================


class AppointmentSlotCreate(BaseModel):
    """Schema for creating an appointment slot."""

    doctor_id: int
    clinic_id: int
    slot_datetime: datetime
    duration_minutes: int = Field(30, ge=15, le=120)
    capacity: int = Field(1, ge=1, le=10)


class AppointmentSlotUpdate(BaseModel):
    """Schema for updating an appointment slot."""

    slot_datetime: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=120)
    capacity: Optional[int] = Field(None, ge=1, le=10)
    is_booked: Optional[bool] = None


class AppointmentSlotResponse(AppointmentSlotCreate):
    """Schema for appointment slot response."""

    id: int
    is_booked: bool
    booked_count: int
    available_slots: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Appointment Schemas
# ============================================================================


class AppointmentCreate(BaseModel):
    """Schema for creating an appointment."""

    patient_id: int
    doctor_id: int
    clinic_id: int
    slot_id: int
    reason_for_visit: Optional[str] = Field(None, max_length=500)


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""

    status: Optional[str] = Field(None, pattern="^(pending|confirmed|cancelled|completed|no_show)$")
    reason_for_visit: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class AppointmentCancel(BaseModel):
    """Schema for cancelling an appointment."""

    cancelled_reason: str = Field(..., min_length=1, max_length=500)


class AppointmentResponse(AppointmentCreate):
    """Schema for appointment response."""

    id: int
    status: str
    notes: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppointmentDetailResponse(AppointmentResponse):
    """Detailed appointment response with doctor and clinic info."""

    doctor_name: str
    clinic_name: str
    patient_name: str
    slot_datetime: datetime


# ============================================================================
# Error Schemas
# ============================================================================


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
    error_code: str = "INTERNAL_ERROR"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Schema for validation error responses."""

    detail: str
    errors: dict


# ============================================================================
# Dashboard/Filter Schemas
# ============================================================================


class DoctorSearchFilter(BaseModel):
    """Schema for searching doctors."""

    specialty: Optional[str] = None
    clinic_id: Optional[int] = None
    experience_min: Optional[int] = Field(None, ge=0)
    experience_max: Optional[int] = Field(None, ge=0)


class SlotAvailabilityFilter(BaseModel):
    """Schema for filtering available slots."""

    doctor_id: Optional[int] = None
    clinic_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    specialty: Optional[str] = None
