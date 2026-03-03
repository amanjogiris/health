"""Clinic model for the health_app."""
from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import Column, Index, Integer, String, Text

from app.db.base import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


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


__all__ = ["Clinic"]
