"""Repository for DynamicAppointment records.

Provides typed async methods used exclusively by ``DynamicSlotService``.
All conflict-detection queries needed by the service are also centralised here.
"""
from __future__ import annotations

import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dynamic_appointment import DynamicAppointment, DynamicAppointmentStatus


class DynamicAppointmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, appt_id: int) -> Optional[DynamicAppointment]:
        result = await self.db.execute(
            select(DynamicAppointment).where(
                DynamicAppointment.id == appt_id,
                DynamicAppointment.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_booked_windows_for_date(
        self,
        doctor_id: int,
        date: datetime.date,
    ) -> List[Tuple[datetime.datetime, datetime.datetime]]:
        """Return (start, end) pairs for all active bookings on a given date.

        Used by the factory to mark slots as unavailable.
        """
        day_start = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
        day_end = datetime.datetime.combine(date, datetime.time.max, tzinfo=datetime.timezone.utc)

        result = await self.db.execute(
            select(DynamicAppointment.start_time, DynamicAppointment.end_time).where(
                DynamicAppointment.doctor_id == doctor_id,
                DynamicAppointment.is_active == True,
                DynamicAppointment.status != DynamicAppointmentStatus.CANCELLED,
                DynamicAppointment.start_time >= day_start,
                DynamicAppointment.start_time <= day_end,
            )
        )
        return [(row.start_time, row.end_time) for row in result.all()]

    async def has_conflict(
        self,
        doctor_id: int,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Return True when an active booking overlaps [start_time, end_time).

        Conflict condition:
            existing.start_time < new_end  AND  existing.end_time > new_start
        """
        stmt = select(DynamicAppointment).where(
            DynamicAppointment.doctor_id == doctor_id,
            DynamicAppointment.is_active == True,
            DynamicAppointment.status != DynamicAppointmentStatus.CANCELLED,
            DynamicAppointment.start_time < end_time,
            DynamicAppointment.end_time > start_time,
        )
        if exclude_id is not None:
            stmt = stmt.where(DynamicAppointment.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_by_doctor(
        self,
        doctor_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DynamicAppointment]:
        result = await self.db.execute(
            select(DynamicAppointment)
            .where(
                DynamicAppointment.doctor_id == doctor_id,
                DynamicAppointment.is_active == True,
            )
            .order_by(DynamicAppointment.start_time.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_patient(
        self,
        patient_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DynamicAppointment]:
        result = await self.db.execute(
            select(DynamicAppointment)
            .where(
                DynamicAppointment.patient_id == patient_id,
                DynamicAppointment.is_active == True,
            )
            .order_by(DynamicAppointment.start_time.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DynamicAppointment]:
        result = await self.db.execute(
            select(DynamicAppointment)
            .where(DynamicAppointment.is_active == True)
            .order_by(DynamicAppointment.start_time.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(
        self,
        doctor_id: int,
        patient_id: int,
        clinic_id: int,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        reason_for_visit: Optional[str] = None,
    ) -> DynamicAppointment:
        """Persist a new booking.  Conflict check must be done *before* calling this."""
        appt = DynamicAppointment(
            doctor_id=doctor_id,
            patient_id=patient_id,
            clinic_id=clinic_id,
            start_time=start_time,
            end_time=end_time,
            reason_for_visit=reason_for_visit,
        )
        self.db.add(appt)
        # Flush to get the id and trigger the DB unique constraint *before* commit;
        # any IntegrityError (race condition) surfaces here and will be rolled back.
        await self.db.flush()
        return appt

    async def cancel(
        self, appt_id: int, reason: str
    ) -> Optional[DynamicAppointment]:
        appt = await self.get_by_id(appt_id)
        if appt is None:
            return None
        appt.status = DynamicAppointmentStatus.CANCELLED
        appt.cancelled_at = datetime.datetime.now(tz=datetime.timezone.utc)
        appt.cancelled_reason = reason
        self.db.add(appt)
        await self.db.commit()
        await self.db.refresh(appt)
        return appt
