"""Appointment service – booking and cancellation with race-condition protection."""
from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import AppointmentStatus
from app.models.user import User, UserRole
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.slot_repository import SlotRepository
from app.schemas.appointment_schema import AppointmentBook, AppointmentCancel, AppointmentResponse
from app.utils.exceptions import BusinessRuleError, ForbiddenError, NotFoundError


class AppointmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = AppointmentRepository(db)
        self._slot_repo = SlotRepository(db)

    async def book(self, payload: AppointmentBook) -> AppointmentResponse:
        """Book an appointment.

        Uses SELECT FOR UPDATE on the slot row to prevent concurrent double-booking.
        """
        async with self.db.begin_nested():
            # Lock the row so concurrent requests queue up
            slot = await self._slot_repo.get_by_id_with_lock(payload.slot_id)
            if slot is None:
                raise NotFoundError("Slot")
            if slot.booked_count >= slot.capacity:
                raise BusinessRuleError("The selected slot is fully booked.")

            # Guard against the same patient booking the same slot twice
            existing = await self._repo.get_by_slot_id(payload.slot_id)
            if existing and existing.patient_id == payload.patient_id:
                raise BusinessRuleError("You have already booked this slot.")

            appt = await self._repo.create(
                patient_id=payload.patient_id,
                doctor_id=payload.doctor_id,
                slot_id=payload.slot_id,
                clinic_id=payload.clinic_id,
                reason_for_visit=payload.reason_for_visit,
                status=AppointmentStatus.PENDING,
            )

            # Increment booked count; mark as fully booked when capacity is reached
            new_count = slot.booked_count + 1
            await self._slot_repo.update(
                slot.id,
                booked_count=new_count,
                is_booked=(new_count >= slot.capacity),
            )

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
            and appt.doctor_id != current_user.id
        ):
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

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[AppointmentResponse]:
        data = await self._repo.list_all(skip=skip, limit=limit)
        return [AppointmentResponse.model_validate(a) for a in data]
