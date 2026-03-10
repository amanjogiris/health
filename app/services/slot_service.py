"""Slot service – creation, listing and deletion with overlap validation."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.slot_repository import SlotRepository
from app.schemas.slot_schema import SlotCreate, SlotResponse
from app.utils.exceptions import BusinessRuleError, NotFoundError


class SlotService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = SlotRepository(db)

    async def create(self, payload: SlotCreate) -> SlotResponse:
        """Create a slot, rejecting if the doctor already has a conflicting one."""
        overlap = await self._repo.has_overlap(
            payload.doctor_id, payload.start_time, payload.end_time
        )
        if overlap:
            raise BusinessRuleError(
                "The doctor already has a slot that overlaps with the requested time window."
            )
        slot = await self._repo.create(
            doctor_id=payload.doctor_id,
            clinic_id=payload.clinic_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            capacity=payload.capacity,
        )
        return SlotResponse.model_validate(slot)

    async def list_available(
        self,
        doctor_id: Optional[int] = None,
        clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
        include_all: bool = False,
    ) -> List[SlotResponse]:
        slots = await self._repo.list_available(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
            include_all=include_all,
        )
        return [SlotResponse.model_validate(s) for s in slots]

    async def delete(self, slot_id: int) -> None:
        slot = await self._repo.get_by_id(slot_id)
        if slot is None:
            raise NotFoundError("Slot")
        if slot.booked_count > 0:
            raise BusinessRuleError("Cannot delete a slot that has active bookings.")
        await self._repo.soft_delete(slot_id)
