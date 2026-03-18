"""Repository for DoctorLeave CRUD operations."""
from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor_leave import DoctorLeave


class DoctorLeaveRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        doctor_id: int,
        date: datetime.date,
        is_full_day: bool,
        start_time: Optional[datetime.time],
        end_time: Optional[datetime.time],
        reason: Optional[str],
    ) -> DoctorLeave:
        leave = DoctorLeave(
            doctor_id=doctor_id,
            date=date,
            is_full_day=is_full_day,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
        )
        self.db.add(leave)
        await self.db.flush()
        await self.db.refresh(leave)
        return leave

    async def get_by_id(self, leave_id: int) -> Optional[DoctorLeave]:
        result = await self.db.execute(
            select(DoctorLeave).where(DoctorLeave.id == leave_id)
        )
        return result.scalar_one_or_none()

    async def get_by_doctor(
        self,
        doctor_id: int,
        date_from: Optional[datetime.date] = None,
        date_to: Optional[datetime.date] = None,
    ) -> List[DoctorLeave]:
        """Return all leaves for a doctor, optionally filtered by date range."""
        filters = [DoctorLeave.doctor_id == doctor_id]
        if date_from is not None:
            filters.append(DoctorLeave.date >= date_from)
        if date_to is not None:
            filters.append(DoctorLeave.date <= date_to)
        result = await self.db.execute(
            select(DoctorLeave)
            .where(and_(*filters))
            .order_by(DoctorLeave.date, DoctorLeave.start_time)
        )
        return list(result.scalars().all())

    async def get_by_doctor_and_date(
        self, doctor_id: int, date: datetime.date
    ) -> List[DoctorLeave]:
        """Return all leave records for a doctor on a specific date."""
        result = await self.db.execute(
            select(DoctorLeave).where(
                and_(
                    DoctorLeave.doctor_id == doctor_id,
                    DoctorLeave.date == date,
                )
            )
        )
        return list(result.scalars().all())

    async def delete(self, leave_id: int) -> bool:
        leave = await self.get_by_id(leave_id)
        if leave is None:
            return False
        await self.db.delete(leave)
        await self.db.flush()
        return True


__all__ = ["DoctorLeaveRepository"]
