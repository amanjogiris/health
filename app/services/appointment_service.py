"""Appointment service – booking and cancellation with race-condition protection."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.slot_repository import SlotRepository
from app.schemas.appointment_schema import AppointmentBook, AppointmentCancel, AppointmentResponse
from app.schemas.pagination import PaginatedResponse
from app.utils.exceptions import BusinessRuleError, ForbiddenError, NotFoundError


class AppointmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = AppointmentRepository(db)
        self._slot_repo = SlotRepository(db)
        self._doctor_repo = DoctorRepository(db)

    async def book(self, payload: AppointmentBook) -> AppointmentResponse:
        """Book an appointment.

        Uses SELECT FOR UPDATE on the slot row to prevent concurrent double-booking.
        All writes are flushed atomically in one transaction and committed once at
        the end so the row lock is held until the slot count update is also persisted.
        """
        try:
            # Lock the slot row — concurrent requests queue here until we commit
            slot = await self._slot_repo.get_by_id_with_lock(payload.slot_id)
            if slot is None:
                raise NotFoundError("Slot")
            if slot.booked_count >= slot.capacity:
                raise BusinessRuleError("The selected slot is fully booked.")

            # Guard against the same patient booking the same slot twice
            existing = await self._repo.get_by_slot_id(payload.slot_id)
            if existing and existing.patient_id == payload.patient_id:
                raise BusinessRuleError("You have already booked this slot.")

            # Add appointment and flush to get the DB-assigned id without committing
            # (keeps the slot row lock active)
            appt = Appointment(
                patient_id=payload.patient_id,
                doctor_id=payload.doctor_id,
                slot_id=payload.slot_id,
                clinic_id=payload.clinic_id,
                reason_for_visit=payload.reason_for_visit,
                status=AppointmentStatus.BOOKED,
            )
            self.db.add(appt)
            await self.db.flush()

            # Increment booked count on the locked slot object directly
            new_count = slot.booked_count + 1
            slot.booked_count = new_count
            slot.is_booked = new_count >= slot.capacity
            self.db.add(slot)

            # Single commit — atomically persists appointment + slot update
            # and releases the SELECT FOR UPDATE lock
            await self.db.commit()
            await self.db.refresh(appt)

        except Exception:
            await self.db.rollback()
            raise

        return AppointmentResponse.model_validate(appt)

    async def cancel(
        self, appointment_id: int, payload: AppointmentCancel, current_user: User
    ) -> AppointmentResponse:
        appt = await self._repo.get_by_id(appointment_id)
        if appt is None:
            raise NotFoundError("Appointment")

        if (
            current_user.role == UserRole.PATIENT
            and appt.patient_id != current_user.id
        ):
            raise ForbiddenError("You are not authorised to cancel this appointment.")

        if (
            current_user.role == UserRole.DOCTOR
        ):
            doctor = await self._doctor_repo.get_by_user_id(current_user.id)
            if doctor is None or appt.doctor_id != doctor.id:
                raise ForbiddenError("You are not authorised to cancel this appointment.")

        if appt.status == AppointmentStatus.CANCELLED:
            raise BusinessRuleError("Appointment is already cancelled.")

        cancelled = await self._repo.cancel(appointment_id, payload.cancelled_reason)

        # Free up the slot
        slot = await self._slot_repo.get_by_id(appt.slot_id)
        if slot:
            new_count = max(0, slot.booked_count - 1)
            await self._slot_repo.update(slot.id, booked_count=new_count, is_booked=False)

        return AppointmentResponse.model_validate(cancelled)

    async def get(self, appointment_id: int) -> AppointmentResponse:
        appt = await self._repo.get_by_id(appointment_id)
        if appt is None:
            raise NotFoundError("Appointment")
        return AppointmentResponse.model_validate(appt)

    async def get_with_ownership_check(
        self, appointment_id: int, current_user: User
    ) -> AppointmentResponse:
        """Return appointment only if the user is the owner, the assigned doctor, or admin."""
        appt = await self._repo.get_by_id(appointment_id)
        if appt is None:
            raise NotFoundError("Appointment")

        is_admin = current_user.role.value in ("admin", "super_admin")
        is_patient_owner = (
            current_user.role == UserRole.PATIENT and appt.patient_id == current_user.id
        )
        is_doctor_owner = (
            current_user.role == UserRole.DOCTOR and appt.doctor_id == current_user.id
        )
        if not (is_admin or is_patient_owner or is_doctor_owner):
            raise ForbiddenError("You are not authorised to view this appointment.")

        return AppointmentResponse.model_validate(appt)

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PaginatedResponse[AppointmentResponse]:
        base_filters = [Appointment.is_active == True]
        if status and status.lower() != 'all':
            from sqlalchemy import cast, String
            base_filters.append(cast(Appointment.status, String) == status.upper())
        if search:
            q = f"%{search}%"
            from sqlalchemy import or_, cast, String
            base_filters.append(
                or_(
                    User.name.ilike(q),
                    Appointment.reason_for_visit.ilike(q),
                    cast(Appointment.status, String).ilike(q),
                )
            )

        join_stmt = (
            select(Appointment)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(User, Patient.user_id == User.id)
            .where(*base_filters)
        )

        count_result = await self.db.execute(
            select(func.count()).select_from(join_stmt.subquery())
        )
        total = count_result.scalar_one()

        data_result = await self.db.execute(
            select(Appointment, User.name)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(User, Patient.user_id == User.id)
            .where(*base_filters)
            .order_by(Appointment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = data_result.all()
        out = []
        for appt, pname in rows:
            resp = AppointmentResponse.model_validate(appt)
            resp.patient_name = pname
            out.append(resp)
        return PaginatedResponse(items=out, total=total, skip=skip, limit=limit)
