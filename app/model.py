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

from sqlalchemy.orm import declarative_base, declarative_mixin

# Password hashing: prefer passlib bcrypt
try:
    from passlib.hash import bcrypt  # type: ignore
except Exception:  # pragma: no cover - explicit runtime error if missing
    bcrypt = None  # type: ignore


Base = declarative_base()


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


__all__ = ["Base", "User", "UserRole", "TimestampMixin", "SoftDeleteMixin"]
