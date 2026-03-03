"""Doctor model for the health_app."""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import Column, Index, Integer, String, Text

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


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


__all__ = ["Doctor"]
