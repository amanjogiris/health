"""User model for the health_app."""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Dict, Optional

import bcrypt as _bcrypt
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Index,
    Integer,
    String,
    Text,
)

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class UserRole(enum.Enum):
    """Canonical user roles used for authorization and behaviour.

    Keep values lowercase for easier checks when reading from JSON/HTTP.
    Role hierarchy (highest → lowest): SUPER_ADMIN > ADMIN > DOCTOR > PATIENT
    """

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


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
    role: UserRole = Column(
        SAEnum(UserRole, name="user_roles", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.PATIENT,
    )
    is_verified: bool = Column(Boolean, default=False, nullable=False)
    last_login: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<User id={self.id} email={self.email} role={self.role.value}>"

    # ---- Password helpers -------------------------------------------------
    def set_password(self, password: str) -> None:
        """Hash and store the user's password using bcrypt."""
        self.password_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()

    def verify_password(self, password: str) -> bool:
        """Return True if *password* matches the stored hash."""
        try:
            return _bcrypt.checkpw(password.encode(), self.password_hash.encode())
        except Exception:
            return False

    # ---- Utility methods --------------------------------------------------
    def to_dict(self, include_private: bool = False) -> Dict[str, Any]:
        """Return a serializable representation of the user."""
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


__all__ = ["User", "UserRole"]
