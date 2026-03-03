"""Patient model for the health_app."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Column, Index, Integer, String, Text

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


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


__all__ = ["Patient"]
