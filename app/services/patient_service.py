"""Patient service – profile retrieval and updates."""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.patient_repository import PatientRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.patient_schema import PatientUpdate, PatientResponse, AdminPatientUpdate
from app.schemas.appointment_schema import AppointmentResponse
from app.schemas.pagination import PaginatedResponse
from app.utils.exceptions import NotFoundError, ForbiddenError
from app.models.user import User, UserRole
from app.models.patient import Patient
from typing import List, Optional


class PatientService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = PatientRepository(db)
        self._user_repo = UserRepository(db)
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

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
    ) -> PaginatedResponse[PatientResponse]:
        base_filters = [Patient.is_active == True]
        if search:
            q = f"%{search}%"
            base_filters.append(
                or_(User.name.ilike(q), User.email.ilike(q))
            )

        join_stmt = (
            select(Patient)
            .join(User, Patient.user_id == User.id)
            .where(*base_filters)
        )
        count_result = await self.db.execute(
            select(func.count()).select_from(join_stmt.subquery())
        )
        total = count_result.scalar_one()

        data_result = await self.db.execute(
            select(Patient, User)
            .join(User, Patient.user_id == User.id)
            .where(*base_filters)
            .offset(skip)
            .limit(limit)
        )
        rows = data_result.all()
        responses = []
        for patient, user in rows:
            resp = PatientResponse.model_validate(patient)
            resp.patient_name = user.name
            resp.email = user.email
            resp.mobile_no = getattr(user, "mobile_no", None)
            resp.address = getattr(user, "address", None)
            responses.append(resp)
        return PaginatedResponse(items=responses, total=total, skip=skip, limit=limit)

    async def update_with_ownership_check(
        self, patient_id: int, payload: PatientUpdate, current_user: User
    ) -> PatientResponse:
        patient = await self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient")
        is_admin = current_user.role.value in ("admin", "super_admin")
        if not is_admin and patient.user_id != current_user.id:
            raise ForbiddenError("You are not authorised to update this patient.")
        updated = await self._repo.update(patient_id, **payload.model_dump(exclude_unset=True))
        return PatientResponse.model_validate(updated)

    async def admin_full_update(
        self, patient_id: int, payload: AdminPatientUpdate
    ) -> PatientResponse:
        """Admin: update both user-level and patient-profile fields."""
        patient = await self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient")
        # Update user-level fields
        user_fields = {k: v for k, v in {
            "name": payload.name,
            "email": payload.email,
            "mobile_no": payload.mobile_no,
            "address": payload.address,
        }.items() if v is not None}
        if user_fields:
            await self._user_repo.update(patient.user_id, **user_fields)
        # Update patient-profile fields
        profile_fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items()
                         if k not in ("name", "email", "mobile_no", "address") and v is not None}
        if profile_fields:
            await self._repo.update(patient_id, **profile_fields)
        # Re-fetch enriched response
        result = await self.list_all(skip=0, limit=1000)
        for p in result.items:
            if p.id == patient_id:
                return p
        return await self.get(patient_id)

    async def deactivate(self, patient_id: int) -> None:
        patient = await self._repo.get_by_id(patient_id)
        if patient is None:
            raise NotFoundError("Patient")
        patient.is_active = False
        self.db.add(patient)
        await self.db.commit()

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
