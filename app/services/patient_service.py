"""Patient service – profile retrieval and updates."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.patient_repository import PatientRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.patient_schema import PatientUpdate, PatientResponse
from app.schemas.appointment_schema import AppointmentResponse
from app.utils.exceptions import NotFoundError, ForbiddenError
from app.models.user import User, UserRole
from typing import List


class PatientService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = PatientRepository(db)
        self._appt_repo = AppointmentRepository(db)

    async def get(self, patient_id: int) -> PatientResponse:
        patient = await self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient")
        return PatientResponse.model_validate(patient)

    async def get_with_ownership_check(
        self, patient_id: int, current_user: User
    ) -> PatientResponse:
        """Return patient profile only if requester is the owner or admin."""
        patient = await self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient")

        is_admin = current_user.role.value in ("admin", "super_admin")
        if not is_admin and patient.user_id != current_user.id:
            raise ForbiddenError("You are not authorised to view this patient.")

        return PatientResponse.model_validate(patient)

    async def update(
        self, patient_id: int, payload: PatientUpdate, current_user: User
    ) -> PatientResponse:
        patient = await self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient")
        # Only the patient themselves can update their profile
        if patient.user_id != current_user.id:
            raise ForbiddenError("You are not authorised to update this patient.")
        updated = await self._repo.update(patient_id, **payload.model_dump(exclude_unset=True))
        return PatientResponse.model_validate(updated)

    async def get_appointments(
        self, patient_id: int, skip: int = 0, limit: int = 100
    ) -> List[AppointmentResponse]:
        data = await self._appt_repo.list_by_patient(patient_id, skip, limit)
        return [AppointmentResponse.model_validate(a) for a in data]
