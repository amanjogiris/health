"""Doctor service – CRUD for doctors + availability + slot generation."""
from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.slot_repository import SlotRepository
from app.repositories.user_repository import UserRepository
from app.schemas.doctor_schema import (
    AvailabilityInput,
    AvailabilityResponse,
    AdminDoctorUpdate,
    DoctorCreate,
    DoctorRegister,
    DoctorResponse,
    DoctorUpdate,
)
from app.schemas.appointment_schema import AppointmentResponse
from app.utils.exceptions import ConflictError, NotFoundError


def _parse_time(t: str) -> datetime.time:
    """Parse 'HH:MM' string to a time object."""
    h, m = map(int, t.split(":"))
    return datetime.time(h, m)


class DoctorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = DoctorRepository(db)
        self._appt_repo = AppointmentRepository(db)
        self._avail_repo = AvailabilityRepository(db)
        self._slot_repo = SlotRepository(db)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _generate_slots(
        self,
        doctor_id: int,
        clinic_id: int,
        duration_minutes: int,
        availability_inputs: List[AvailabilityInput],
        days_ahead: int = 7,
    ) -> int:
        """Generate appointment slots for the next *days_ahead* days.

        Rules:
        - Each slot = duration_minutes long.
        - Slots follow doctor's weekly availability.
        - Duplicate start_times are skipped (idempotent).
        - Returns the number of newly created slots.
        """
        today = datetime.date.today()
        date_from = datetime.datetime.combine(today, datetime.time.min)
        date_to = datetime.datetime.combine(today + datetime.timedelta(days=days_ahead), datetime.time.min)

        existing = await self._slot_repo.get_existing_start_times(doctor_id, date_from, date_to)

        slots_to_add: List[dict] = []
        for day_offset in range(days_ahead):
            current_date = today + datetime.timedelta(days=day_offset)
            current_dow = current_date.weekday()  # 0 = Monday

            for avail in availability_inputs:
                if avail.day_of_week != current_dow:
                    continue

                start_t = _parse_time(avail.start_time)
                end_t = _parse_time(avail.end_time)

                if start_t >= end_t:
                    continue  # invalid window – skip silently

                slot_start = datetime.datetime.combine(current_date, start_t)
                slot_end_max = datetime.datetime.combine(current_date, end_t)

                while slot_start + datetime.timedelta(minutes=duration_minutes) <= slot_end_max:
                    slot_end = slot_start + datetime.timedelta(minutes=duration_minutes)
                    if slot_start not in existing:
                        slots_to_add.append(
                            {
                                "doctor_id": doctor_id,
                                "clinic_id": clinic_id,
                                "start_time": slot_start,
                                "end_time": slot_end,
                            }
                        )
                        existing.add(slot_start)
                    slot_start = slot_end

        if slots_to_add:
            await self._slot_repo.create_bulk(slots_to_add)
            await self.db.commit()
            return len(slots_to_add)
        return 0

    def _build_response(
        self,
        doctor: Doctor,
        doctor_name: Optional[str] = None,
        clinic_name: Optional[str] = None,
        email: Optional[str] = None,
        mobile_no: Optional[str] = None,
        availability: Optional[List[AvailabilityResponse]] = None,
    ) -> DoctorResponse:
        resp = DoctorResponse.model_validate(doctor)
        resp.doctor_name = doctor_name
        resp.clinic_name = clinic_name
        resp.email = email
        resp.mobile_no = mobile_no
        resp.availability = availability
        return resp

    # ── Public API ────────────────────────────────────────────────────────────

    async def create(self, payload: DoctorCreate) -> DoctorResponse:
        doctor = await self._repo.create(**payload.model_dump())
        return DoctorResponse.model_validate(doctor)

    async def get(self, doctor_id: int) -> DoctorResponse:
        doctor = await self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")
        avail = await self._avail_repo.get_by_doctor(doctor_id)
        avail_resp = [AvailabilityResponse.model_validate(a) for a in avail]
        return self._build_response(doctor, availability=avail_resp)

    async def get_profile_by_user(self, user_id: int) -> DoctorResponse:
        doctor = await self._repo.get_by_user_id(user_id)
        if doctor is None:
            raise NotFoundError("Doctor profile")
        avail = await self._avail_repo.get_by_doctor(doctor.id)
        avail_resp = [AvailabilityResponse.model_validate(a) for a in avail]
        return self._build_response(doctor, availability=avail_resp)

    async def update_profile_by_user(self, user_id: int, payload: DoctorUpdate) -> DoctorResponse:
        doctor = await self._repo.get_by_user_id(user_id)
        if doctor is None:
            raise NotFoundError("Doctor profile")
        updated = await self._repo.update(doctor.id, **payload.model_dump(exclude_unset=True))
        return DoctorResponse.model_validate(updated)

    async def get_appointments_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AppointmentResponse]:
        doctor = await self._repo.get_by_user_id(user_id)
        if doctor is None:
            raise NotFoundError("Doctor profile")
        data = await self._appt_repo.list_by_doctor(doctor.id, skip, limit)
        # Batch-load patient names
        patient_ids = list({a.patient_id for a in data})
        if patient_ids:
            result = await self.db.execute(select(User).where(User.id.in_(patient_ids)))
            user_map = {u.id: u.name for u in result.scalars().all()}
        else:
            user_map = {}
        responses = []
        for a in data:
            r = AppointmentResponse.model_validate(a)
            r.patient_name = user_map.get(a.patient_id)
            responses.append(r)
        return responses

    async def list_all(
        self,
        specialty: Optional[str] = None,
        clinic_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DoctorResponse]:
        rows = await self._repo.list_all_enriched(
            skip=skip, limit=limit, specialty=specialty, clinic_id=clinic_id
        )
        return [
            self._build_response(doctor, doctor_name=user_name, clinic_name=c_name, email=u_email, mobile_no=u_mobile)
            for doctor, user_name, c_name, u_email, u_mobile in rows
        ]

    async def update(self, doctor_id: int, payload: DoctorUpdate) -> DoctorResponse:
        doctor = await self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")
        updated = await self._repo.update(doctor_id, **payload.model_dump(exclude_unset=True))
        return DoctorResponse.model_validate(updated)

    async def admin_full_update(self, doctor_id: int, payload: AdminDoctorUpdate) -> DoctorResponse:
        """Admin: update user-level fields (name, email, mobile_no) + doctor-profile fields."""
        doctor = await self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")
        user_field_keys = {"name", "email", "mobile_no"}
        user_fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items()
                       if k in user_field_keys and v is not None}
        if user_fields:
            user_repo = UserRepository(self.db)
            await user_repo.update(doctor.user_id, **user_fields)
        doctor_fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items()
                         if k not in user_field_keys and v is not None}
        if doctor_fields:
            await self._repo.update(doctor_id, **doctor_fields)
        # Return enriched response by re-fetching via list_all
        rows = await self._repo.list_all_enriched(skip=0, limit=1000)
        for doc, user_name, c_name, u_email, u_mobile in rows:
            if doc.id == doctor_id:
                return self._build_response(doc, doctor_name=user_name, clinic_name=c_name, email=u_email, mobile_no=u_mobile)
        doctor = await self._repo.get_by_id(doctor_id)
        return DoctorResponse.model_validate(doctor)

    async def delete(self, doctor_id: int) -> None:
        doctor = await self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")
        await self._repo.update(doctor_id, is_active=False)

    async def get_availability(self, doctor_id: int) -> List[AvailabilityResponse]:
        doctor = await self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")
        avail = await self._avail_repo.get_by_doctor(doctor_id)
        return [AvailabilityResponse.model_validate(a) for a in avail]

    async def set_availability(
        self,
        doctor_id: int,
        inputs: List[AvailabilityInput],
        regenerate_slots: bool = True,
    ) -> List[AvailabilityResponse]:
        """Replace doctor availability and (optionally) regenerate slots."""
        doctor = await self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")

        # Validate: start < end for each entry
        for a in inputs:
            if _parse_time(a.start_time) >= _parse_time(a.end_time):
                raise ValueError(
                    f"start_time must be before end_time for day {a.day_of_week}."
                )

        items = [
            {
                "day_of_week": a.day_of_week,
                "start_time": _parse_time(a.start_time),
                "end_time": _parse_time(a.end_time),
            }
            for a in inputs
        ]
        records = await self._avail_repo.upsert(doctor_id, items)
        await self.db.commit()

        if regenerate_slots and inputs:
            await self._generate_slots(
                doctor_id=doctor_id,
                clinic_id=doctor.clinic_id,
                duration_minutes=doctor.consultation_duration_minutes,
                availability_inputs=inputs,
            )

        results = await self._avail_repo.get_by_doctor(doctor_id)
        return [AvailabilityResponse.model_validate(r) for r in results]

    async def register_with_user(self, payload: DoctorRegister) -> DoctorResponse:
        """Create user (role=doctor) + doctor profile + availability + slots atomically."""
        user_repo = UserRepository(self.db)
        existing = await user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictError("Email is already registered.")

        user = User(
            name=payload.name,
            email=payload.email,
            role=UserRole.DOCTOR,
            mobile_no=payload.mobile_no,
            is_verified=True,
        )
        user.set_password(payload.password)
        self.db.add(user)
        await self.db.flush()  # get user.id

        doctor = Doctor(
            user_id=user.id,
            clinic_id=payload.clinic_id,
            specialty=payload.specialty,
            license_number=payload.license_number,
            qualifications=payload.qualifications,
            experience_years=payload.experience_years,
            max_patients_per_day=payload.max_patients_per_day,
            consultation_duration_minutes=payload.consultation_duration_minutes,
        )
        self.db.add(doctor)
        await self.db.flush()  # get doctor.id

        # Persist availability
        if payload.availability:
            items = [
                {
                    "day_of_week": a.day_of_week,
                    "start_time": _parse_time(a.start_time),
                    "end_time": _parse_time(a.end_time),
                }
                for a in payload.availability
            ]
            await self._avail_repo.create_bulk(doctor.id, items)

        await self.db.commit()
        await self.db.refresh(doctor)

        # Generate slots outside the main transaction
        if payload.availability:
            await self._generate_slots(
                doctor_id=doctor.id,
                clinic_id=doctor.clinic_id,
                duration_minutes=doctor.consultation_duration_minutes,
                availability_inputs=payload.availability,
            )

        avail = await self._avail_repo.get_by_doctor(doctor.id)
        avail_resp = [AvailabilityResponse.model_validate(a) for a in avail]
        return self._build_response(
            doctor,
            doctor_name=payload.name,
            clinic_name=None,
            availability=avail_resp,
        )


