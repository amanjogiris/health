"""Patient repository."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: int, **kwargs) -> Patient:
        patient = Patient(user_id=user_id, **kwargs)
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def get_by_id(self, patient_id: int) -> Optional[Patient]:
        result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id, Patient.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Optional[Patient]:
        result = await self.db.execute(
            select(Patient).where(Patient.user_id == user_id, Patient.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(self, patient_id: int, **kwargs) -> Optional[Patient]:
        patient = await self.get_by_id(patient_id)
        if patient is None:
            return None
        for k, v in kwargs.items():
            if hasattr(patient, k) and v is not None:
                setattr(patient, k, v)
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        result = await self.db.execute(
            select(Patient).where(Patient.is_active == True).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
