"""Clinic service."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.repositories.clinic_repository import ClinicRepository
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.clinic_schema import ClinicCreate, ClinicUpdate, ClinicResponse
from app.schemas.doctor_schema import DoctorResponse
from app.schemas.pagination import PaginatedResponse
from app.utils.exceptions import NotFoundError


class ClinicService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = ClinicRepository(db)
        self._doctor_repo = DoctorRepository(db)

    async def create(self, payload: ClinicCreate) -> ClinicResponse:
        clinic = await self._repo.create(**payload.model_dump())
        return ClinicResponse.model_validate(clinic)

    async def get(self, clinic_id: int) -> ClinicResponse:
        clinic = await self._repo.get_by_id(clinic_id)
        if clinic is None:
            raise NotFoundError("Clinic")
        return ClinicResponse.model_validate(clinic)

    async def list_all(
        self,
        city: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
    ) -> PaginatedResponse[ClinicResponse]:
        base_filters = [Clinic.is_active == True]
        if city:
            base_filters.append(Clinic.city == city)
        if search:
            q = f"%{search}%"
            base_filters.append(
                or_(Clinic.name.ilike(q), Clinic.city.ilike(q), Clinic.address.ilike(q))
            )

        count_result = await self.db.execute(
            select(func.count()).select_from(Clinic).where(*base_filters)
        )
        total = count_result.scalar_one()

        data_result = await self.db.execute(
            select(Clinic).where(*base_filters).offset(skip).limit(limit)
        )
        clinics = list(data_result.scalars().all())
        return PaginatedResponse(
            items=[ClinicResponse.model_validate(c) for c in clinics],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_doctors(self, clinic_id: int) -> List[DoctorResponse]:
        clinic = await self._repo.get_by_id(clinic_id)
        if clinic is None:
            raise NotFoundError("Clinic")
        doctors = await self._doctor_repo.list_by_clinic(clinic_id)
        return [DoctorResponse.model_validate(d) for d in doctors]

    async def update(self, clinic_id: int, payload: ClinicUpdate) -> ClinicResponse:
        clinic = await self._repo.get_by_id(clinic_id)
        if clinic is None:
            raise NotFoundError("Clinic")
        updated = await self._repo.update(clinic_id, **payload.model_dump(exclude_unset=True))
        return ClinicResponse.model_validate(updated)

    async def delete(self, clinic_id: int) -> None:
        clinic = await self._repo.get_by_id(clinic_id)
        if clinic is None:
            raise NotFoundError("Clinic")
        await self._repo.delete(clinic_id)
