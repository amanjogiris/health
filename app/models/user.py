"""Database models for the health_app.

This module defines a secure, extensible `User` model suitable for roles
like `admin`, `doctor`, and `patient`. Password hashing uses `passlib`'s
bcrypt algorithm — install with `pip install passlib[bcrypt]`.

Design goals:
- Secure password hashing (bcrypt via passlib)
- Clear role enum for authorization checks
- Timestamp and soft-delete mixins for common behavior
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum as SAEnum,
    Boolean,
    DateTime,
    Text,
    func,
    Index,
)

from sqlalchemy.orm import declarative_mixin
from app.db.base import Base
# Password hashing: prefer passlib bcrypt
try:
    from passlib.hash import bcrypt  # type: ignore
except Exception:  # pragma: no cover - explicit runtime error if missing
    bcrypt = None  # type: ignore


class UserRole(enum.Enum):
    """Canonical user roles used for authorization and behaviour.

    Keep values lowercase for easier checks when reading from JSON/HTTP.
    """

    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


@declarative_mixin
class TimestampMixin:
    """Adds `created_at` and `updated_at` columns with DB-side defaults."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


@declarative_mixin
class SoftDeleteMixin:
    """Adds a simple `is_active` flag instead of hard deletes."""

    is_active = Column(Boolean, default=True, nullable=False)


class User(Base, TimestampMixin, SoftDeleteMixin):
    """Primary user model.

    - `email` is unique and indexed for fast lookups.
    - `role` is an Enum backed by `UserRole` for clear role checks.
    """

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email"),)

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(150), nullable=False)
    email: str = Column(String(255), nullable=False, unique=True, index=True)
    password_hash: str = Column(String(128), nullable=False)
    mobile_no: Optional[str] = Column(String(20), nullable=True)
    address: Optional[str] = Column(Text, nullable=True)
    image: Optional[str] = Column(String(255), nullable=True)  # URL or path to user's image
    role: UserRole = Column(SAEnum(UserRole, name="user_roles"), nullable=False, default=UserRole.PATIENT)
    is_verified: bool = Column(Boolean, default=False, nullable=False)
    last_login: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<User id={self.id} email={self.email} role={self.role.value}>"

    # ---- Password helpers -------------------------------------------------
    @staticmethod
    def _require_bcrypt() -> None:
        if bcrypt is None:
            raise RuntimeError(
                "passlib is required for secure password hashing. "
                "Install with: pip install passlib[bcrypt]"
            )

    def set_password(self, password: str) -> None:
        """Hash and set the user's password.

        This mutates the instance's `password_hash`. The application should
        persist the instance using the current SQLAlchemy session.
        """

        self._require_bcrypt()
        # bcrypt.hash will generate a unique salt per-hash and store it in
        # the resulting string. We keep the output length small (bcrypt uses ~60).
        self.password_hash = bcrypt.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify a plaintext password against the stored hash."""

        self._require_bcrypt()
        try:
            return bcrypt.verify(password, self.password_hash)
        except Exception:
            # Any exception here means verification failed or hash is malformed
            return False

    # ---- Utility methods --------------------------------------------------
    def to_dict(self, include_private: bool = False) -> Dict[str, Any]:
        """Return a serializable representation of the user.

        By default, sensitive fields (like `password_hash`) are excluded.
        Pass `include_private=True` only when the output is used in a
        trusted, internal context (e.g. admin debugging).
        """

        data: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "mobile_no": self.mobile_no,
            "address": self.address,
            "image": self.image,
            "role": self.role.value if isinstance(self.role, UserRole) else str(self.role),
            "is_verified": self.is_verified,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_private:
            data["password_hash"] = self.password_hash

        return data


class Patient(Base, TimestampMixin, SoftDeleteMixin):
    """Patient model extending User with patient-specific fields."""

    __tablename__ = "patients"
    __table_args__ = (Index("ix_patients_user_id", "user_id"),)

    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, nullable=False, unique=True, index=True)
    date_of_birth: Optional[str] = Column(String(10), nullable=True)  # YYYY-MM-DD format
    blood_group: Optional[str] = Column(String(5), nullable=True)
    allergies: Optional[str] = Column(Text, nullable=True)
    emergency_contact: Optional[str] = Column(String(20), nullable=True)

    def __repr__(self) -> str:
        return f"<Patient id={self.id} user_id={self.user_id}>"


class Clinic(Base, TimestampMixin, SoftDeleteMixin):
    """Clinic model for managing healthcare centers."""

    __tablename__ = "clinics"
    __table_args__ = (Index("ix_clinics_name", "name"),)

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String(255), nullable=False)
    address: str = Column(Text, nullable=False)
    phone: str = Column(String(20), nullable=False)
    email: str = Column(String(255), nullable=True)
    city: str = Column(String(100), nullable=False)
    state: str = Column(String(100), nullable=False)
    zip_code: str = Column(String(10), nullable=False)

    def __repr__(self) -> str:
        return f"<Clinic id={self.id} name={self.name}>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Doctor(Base, TimestampMixin, SoftDeleteMixin):
    """Doctor model with specialty and clinic mapping."""

    __tablename__ = "doctors"
    __table_args__ = (
        Index("ix_doctors_user_id", "user_id"),
        Index("ix_doctors_clinic_id", "clinic_id"),
    )

    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(Integer, nullable=False, unique=True, index=True)
    clinic_id: int = Column(Integer, nullable=False, index=True)
    specialty: str = Column(String(100), nullable=False)
    license_number: str = Column(String(50), nullable=False, unique=True)
    qualifications: Optional[str] = Column(Text, nullable=True)
    experience_years: int = Column(Integer, default=0, nullable=False)
    max_patients_per_day: int = Column(Integer, default=10, nullable=False)

    def __repr__(self) -> str:
        return f"<Doctor id={self.id} user_id={self.user_id} specialty={self.specialty}>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "clinic_id": self.clinic_id,
            "specialty": self.specialty,
            "license_number": self.license_number,
            "qualifications": self.qualifications,
            "experience_years": self.experience_years,
            "max_patients_per_day": self.max_patients_per_day,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AppointmentSlot(Base, TimestampMixin, SoftDeleteMixin):
    """Appointment slot model for doctor availability."""

    __tablename__ = "appointment_slots"
    __table_args__ = (
        Index("ix_slots_doctor_id", "doctor_id"),
        Index("ix_slots_clinic_id", "clinic_id"),
        Index("ix_slots_slot_datetime", "slot_datetime"),
    )

    id: int = Column(Integer, primary_key=True)
    doctor_id: int = Column(Integer, nullable=False, index=True)
    clinic_id: int = Column(Integer, nullable=False, index=True)
    slot_datetime: datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: int = Column(Integer, default=30, nullable=False)
    is_booked: bool = Column(Boolean, default=False, nullable=False)
    capacity: int = Column(Integer, default=1, nullable=False)
    booked_count: int = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<AppointmentSlot id={self.id} doctor_id={self.doctor_id} slot_datetime={self.slot_datetime}>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "clinic_id": self.clinic_id,
            "slot_datetime": self.slot_datetime.isoformat() if self.slot_datetime else None,
            "duration_minutes": self.duration_minutes,
            "is_booked": self.is_booked,
            "capacity": self.capacity,
            "booked_count": self.booked_count,
            "available_slots": self.capacity - self.booked_count,
        }


class AppointmentStatus(enum.Enum):
    """Status of an appointment."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Appointment(Base, TimestampMixin, SoftDeleteMixin):
    """Appointment booking model."""

    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_patient_id", "patient_id"),
        Index("ix_appointments_doctor_id", "doctor_id"),
        Index("ix_appointments_slot_id", "slot_id"),
    )

    id: int = Column(Integer, primary_key=True)
    patient_id: int = Column(Integer, nullable=False, index=True)
    doctor_id: int = Column(Integer, nullable=False, index=True)
    clinic_id: int = Column(Integer, nullable=False)
    slot_id: int = Column(Integer, nullable=False, unique=True, index=True)
    status: AppointmentStatus = Column(
        SAEnum(AppointmentStatus, name="appointment_status"),
        nullable=False,
        default=AppointmentStatus.PENDING,
    )
    reason_for_visit: Optional[str] = Column(Text, nullable=True)
    notes: Optional[str] = Column(Text, nullable=True)
    cancelled_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Optional[str] = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} patient_id={self.patient_id} doctor_id={self.doctor_id} status={self.status.value}>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "clinic_id": self.clinic_id,
            "slot_id": self.slot_id,
            "status": self.status.value if isinstance(self.status, AppointmentStatus) else str(self.status),
            "reason_for_visit": self.reason_for_visit,
            "notes": self.notes,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancelled_reason": self.cancelled_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


__all__ = [
    "Base",
    "User",
    "Patient",
    "Doctor",
    "Clinic",
    "AppointmentSlot",
    "Appointment",
    "UserRole",
    "AppointmentStatus",
    "TimestampMixin",
    "SoftDeleteMixin",
]
