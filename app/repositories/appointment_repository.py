"""Appointment repository."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus


class AppointmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, **kwargs) -> Appointment:
        appt = Appointment(**kwargs)
        self.db.add(appt)
        await self.db.commit()
        await self.db.refresh(appt)
        return appt

    async def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_slot_id(self, slot_id: int) -> Optional[Appointment]:
        """Return an active, non-cancelled appointment for a given slot."""
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.slot_id == slot_id,
                Appointment.is_active == True,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, appointment_id: int, **kwargs) -> Optional[Appointment]:
        appt = await self.get_by_id(appointment_id)
        if appt is None:
            return None
        for k, v in kwargs.items():
            if hasattr(appt, k) and v is not None:
                setattr(appt, k, v)
        self.db.add(appt)
        await self.db.commit()
        await self.db.refresh(appt)
        return appt

    async def update_fields(self, appointment_id: int, **kwargs) -> Optional[Appointment]:
        """Like update() but allows explicitly setting a field to None or empty string."""
        appt = await self.get_by_id(appointment_id)
        if appt is None:
            return None
        for k, v in kwargs.items():
            if hasattr(appt, k):
                setattr(appt, k, v)
        self.db.add(appt)
        await self.db.commit()
        await self.db.refresh(appt)
        return appt

    async def cancel(self, appointment_id: int, reason: str) -> Optional[Appointment]:
        appt = await self.get_by_id(appointment_id)
        if appt is None:
            return None
        appt.status = AppointmentStatus.CANCELLED
        appt.cancelled_at = datetime.now(timezone.utc)
        appt.cancelled_reason = reason
        self.db.add(appt)
        await self.db.commit()
        await self.db.refresh(appt)
        return appt

    async def list_by_patient(
        self, patient_id: int, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.patient_id == patient_id, Appointment.is_active == True)
            .order_by(Appointment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_doctor(
        self, doctor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.doctor_id == doctor_id, Appointment.is_active == True)
            .order_by(Appointment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .where(Appointment.is_active == True)
            .order_by(Appointment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
