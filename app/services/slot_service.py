"""Slot service – creation, listing, updating, toggling and deletion with overlap validation."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import SlotStatus
from app.repositories.slot_repository import SlotRepository
from app.schemas.slot_schema import SlotCreate, SlotResponse, SlotToggleResponse, SlotUpdate
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
            status=payload.status,
        )
        return SlotResponse.model_validate(slot)

    async def update(self, slot_id: int, payload: SlotUpdate, force: bool = False) -> SlotResponse:
        """Update a slot's time, capacity, or status.

        By default, slots that have been booked (booked_count > 0) cannot change
        their time or capacity — only their status.  Pass ``force=True`` to
        override this guard (admin override).
        """
        slot = await self._repo.get_by_id(slot_id)
        if slot is None:
            raise NotFoundError("Slot")

        # Guard: block time/capacity edits on booked slots unless force=True
        is_booked = slot.booked_count > 0
        if is_booked and not force:
            time_or_capacity_change = (
                payload.start_time is not None
                or payload.end_time is not None
                or payload.capacity is not None
            )
            if time_or_capacity_change:
                raise BusinessRuleError(
                    "Cannot change time or capacity of a slot that has active bookings. "
                    "Pass force=true to override."
                )

        # Derive effective start/end for overlap check
        new_start = payload.start_time or slot.start_time
        new_end = payload.end_time or slot.end_time

        if new_end <= new_start:
            raise BusinessRuleError("end_time must be after start_time.")

        # Check overlap only when time is changing
        if payload.start_time is not None or payload.end_time is not None:
            overlap = await self._repo.has_overlap(
                slot.doctor_id, new_start, new_end, exclude_id=slot_id
            )
            if overlap:
                raise BusinessRuleError(
                    "The updated time window overlaps with another slot for this doctor."
                )

        updated = await self._repo.update(
            slot_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            capacity=payload.capacity,
            status=payload.status,
        )
        if updated is None:
            raise NotFoundError("Slot")
        return SlotResponse.model_validate(updated)

    async def toggle_active(self, slot_id: int) -> SlotToggleResponse:
        """Toggle the is_active flag of a slot.

        An inactive slot is hidden from the public listing but not permanently deleted.
        Slots with active bookings cannot be deactivated.
        """
        slot = await self._repo.get_by_id(slot_id)
        if slot is None:
            raise NotFoundError("Slot")

        if slot.is_active and slot.booked_count > 0:
            raise BusinessRuleError(
                "Cannot deactivate a slot that has active bookings."
            )

        updated = await self._repo.toggle_active(slot_id)
        if updated is None:
            raise NotFoundError("Slot")

        state = "activated" if updated.is_active else "deactivated"
        return SlotToggleResponse(
            id=updated.id,
            is_active=updated.is_active,
            message=f"Slot {slot_id} has been {state}.",
        )

    async def list_available(
        self,
        doctor_id: Optional[int] = None,
        clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[SlotStatus] = None,
        skip: int = 0,
        limit: int = 100,
        include_all: bool = False,
    ) -> List[SlotResponse]:
        slots = await self._repo.list_available(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            date_from=date_from,
            date_to=date_to,
            status=status,
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

