"""Clinic repository."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic


class ClinicRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> Clinic:
        clinic = Clinic(**kwargs)
        self.db.add(clinic)
        await self.db.commit()
        await self.db.refresh(clinic)
        return clinic

    async def get_by_id(self, clinic_id: int) -> Optional[Clinic]:
        result = await self.db.execute(
            select(Clinic).where(Clinic.id == clinic_id, Clinic.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(self, clinic_id: int, **kwargs) -> Optional[Clinic]:
        clinic = await self.get_by_id(clinic_id)
        if clinic is None:
            return None
        for k, v in kwargs.items():
            if hasattr(clinic, k) and v is not None:
                setattr(clinic, k, v)
        self.db.add(clinic)
        await self.db.commit()
        await self.db.refresh(clinic)
        return clinic

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Clinic]:
        result = await self.db.execute(
            select(Clinic).where(Clinic.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_city(self, city: str) -> List[Clinic]:
        result = await self.db.execute(
            select(Clinic).where(Clinic.city == city, Clinic.is_active == True)
        )
        return list(result.scalars().all())

    async def delete(self, clinic_id: int) -> bool:
        clinic = await self.get_by_id(clinic_id)
        if clinic is None:
            return False
        clinic.is_active = False
        self.db.add(clinic)
        await self.db.commit()
        return True
