"""Doctor repository."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.user import User


class DoctorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> Doctor:
        doctor = Doctor(**kwargs)
        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor

    async def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        result = await self.db.execute(
            select(Doctor).where(Doctor.id == doctor_id, Doctor.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Optional[Doctor]:
        result = await self.db.execute(
            select(Doctor).where(Doctor.user_id == user_id, Doctor.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(self, doctor_id: int, **kwargs) -> Optional[Doctor]:
        doctor = await self.get_by_id(doctor_id)
        if doctor is None:
            return None
        for k, v in kwargs.items():
            if hasattr(doctor, k) and v is not None:
                setattr(doctor, k, v)
        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Doctor]:
        result = await self.db.execute(
            select(Doctor).where(Doctor.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_clinic(self, clinic_id: int) -> List[Doctor]:
        result = await self.db.execute(
            select(Doctor).where(Doctor.clinic_id == clinic_id, Doctor.is_active == True)
        )
        return list(result.scalars().all())

    async def search(
        self,
        specialty: Optional[str] = None,
        clinic_id: Optional[int] = None,
    ) -> List[Doctor]:
        stmt = select(Doctor).where(Doctor.is_active == True)
        if specialty:
            stmt = stmt.where(Doctor.specialty == specialty)
        if clinic_id:
            stmt = stmt.where(Doctor.clinic_id == clinic_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_all_enriched(
        self,
        skip: int = 0,
        limit: int = 10,
        specialty: Optional[str] = None,
        clinic_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[Tuple[Doctor, Optional[str], Optional[str], Optional[str], Optional[str]]]:
        """Return (Doctor, doctor_name, clinic_name, user_email, user_mobile_no) rows via JOIN."""
        stmt = (
            select(
                Doctor,
                User.name.label("user_name"),
                Clinic.name.label("clinic_name"),
                User.email.label("user_email"),
                User.mobile_no.label("user_mobile_no"),
            )
            .join(User, User.id == Doctor.user_id, isouter=True)
            .join(Clinic, Clinic.id == Doctor.clinic_id, isouter=True)
            .where(Doctor.is_active == True)
        )
        if specialty:
            stmt = stmt.where(Doctor.specialty == specialty)
        if clinic_id:
            stmt = stmt.where(Doctor.clinic_id == clinic_id)
        if search:
            q = f"%{search}%"
            stmt = stmt.where(
                or_(User.name.ilike(q), Doctor.specialty.ilike(q), Clinic.name.ilike(q))
            )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.all())
