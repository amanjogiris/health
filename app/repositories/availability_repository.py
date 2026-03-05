"""Repository for DoctorAvailability records."""
from __future__ import annotations

import datetime
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import DoctorAvailability


class AvailabilityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_doctor(self, doctor_id: int) -> List[DoctorAvailability]:
        result = await self.db.execute(
            select(DoctorAvailability)
            .where(DoctorAvailability.doctor_id == doctor_id)
            .order_by(DoctorAvailability.day_of_week, DoctorAvailability.start_time)
        )
        return list(result.scalars().all())

    async def delete_by_doctor(self, doctor_id: int) -> None:
        await self.db.execute(
            delete(DoctorAvailability).where(DoctorAvailability.doctor_id == doctor_id)
        )

    async def create_bulk(
        self,
        doctor_id: int,
        items: List[dict],  # [{"day_of_week": int, "start_time": time, "end_time": time}]
    ) -> List[DoctorAvailability]:
        records = [
            DoctorAvailability(
                doctor_id=doctor_id,
                day_of_week=item["day_of_week"],
                start_time=item["start_time"],
                end_time=item["end_time"],
            )
            for item in items
        ]
        self.db.add_all(records)
        await self.db.flush()
        return records

    async def upsert(
        self,
        doctor_id: int,
        items: List[dict],
    ) -> List[DoctorAvailability]:
        """Replace all availability for a doctor atomically."""
        await self.delete_by_doctor(doctor_id)
        return await self.create_bulk(doctor_id, items)
