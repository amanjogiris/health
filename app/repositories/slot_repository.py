"""Appointment slot repository with overlap guard."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Set

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import AppointmentSlot


class SlotRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        doctor_id: int,
        clinic_id: int,
        start_time: datetime,
        end_time: datetime,
        capacity: int = 1,
    ) -> AppointmentSlot:
        slot = AppointmentSlot(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
        )
        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot

    async def has_overlap(
        self, doctor_id: int, start_time: datetime, end_time: datetime, exclude_id: Optional[int] = None
    ) -> bool:
        """Return True if the doctor has an existing active slot that overlaps the given time window."""
        stmt = select(AppointmentSlot).where(
            AppointmentSlot.doctor_id == doctor_id,
            AppointmentSlot.is_active == True,
            AppointmentSlot.start_time < end_time,
            AppointmentSlot.end_time > start_time,
        )
        if exclude_id:
            stmt = stmt.where(AppointmentSlot.id != exclude_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, slot_id: int) -> Optional[AppointmentSlot]:
        result = await self.db.execute(
            select(AppointmentSlot).where(
                AppointmentSlot.id == slot_id,
                AppointmentSlot.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_lock(self, slot_id: int) -> Optional[AppointmentSlot]:
        """Fetch slot with a SELECT FOR UPDATE to prevent concurrent booking."""
        result = await self.db.execute(
            select(AppointmentSlot)
            .where(AppointmentSlot.id == slot_id, AppointmentSlot.is_active == True)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def update(self, slot_id: int, **kwargs) -> Optional[AppointmentSlot]:
        slot = await self.get_by_id(slot_id)
        if slot is None:
            return None
        for k, v in kwargs.items():
            if hasattr(slot, k) and v is not None:
                setattr(slot, k, v)
        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot

    async def soft_delete(self, slot_id: int) -> bool:
        slot = await self.get_by_id(slot_id)
        if slot is None:
            return False
        slot.is_active = False
        self.db.add(slot)
        await self.db.commit()
        return True

    async def list_available(
        self,
        doctor_id: Optional[int] = None,
        clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
        include_all: bool = False,
    ) -> List[AppointmentSlot]:
        stmt = select(AppointmentSlot).where(
            AppointmentSlot.is_active == True,
        )
        if not include_all:
            stmt = stmt.where(AppointmentSlot.booked_count < AppointmentSlot.capacity)
            # Exclude past slots unless the caller explicitly supplies date_from
            if date_from is None:
                stmt = stmt.where(AppointmentSlot.start_time >= func.now())
        if doctor_id:
            stmt = stmt.where(AppointmentSlot.doctor_id == doctor_id)
        if clinic_id:
            stmt = stmt.where(AppointmentSlot.clinic_id == clinic_id)
        if date_from:
            stmt = stmt.where(AppointmentSlot.start_time >= date_from)
        if date_to:
            stmt = stmt.where(AppointmentSlot.start_time <= date_to)
        stmt = stmt.order_by(AppointmentSlot.start_time.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_bulk(self, slots: List[Dict]) -> int:
        """Bulk-add slots without committing (caller commits). Returns count."""
        objs = [AppointmentSlot(**s) for s in slots]
        self.db.add_all(objs)
        await self.db.flush()
        return len(objs)

    async def get_existing_start_times(
        self,
        doctor_id: int,
        date_from: datetime,
        date_to: datetime,
    ) -> Set[datetime]:
        """Return set of existing start_time values to prevent duplicate slots."""
        stmt = select(AppointmentSlot.start_time).where(
            AppointmentSlot.doctor_id == doctor_id,
            AppointmentSlot.is_active == True,
            AppointmentSlot.start_time >= date_from,
            AppointmentSlot.start_time < date_to,
        )
        result = await self.db.execute(stmt)
        return {row[0] for row in result.all()}
