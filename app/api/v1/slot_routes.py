"""Slot routes."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.appointment import SlotStatus
from app.models.user import User
from app.schemas.slot_schema import SlotCreate, SlotResponse, SlotToggleResponse, SlotUpdate
from app.services.slot_service import SlotService

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.post("", response_model=SlotResponse, status_code=201)
async def create_slot(
    payload: SlotCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "super_admin")),
):
    """Admin / Super-Admin: create a single appointment slot.

    **Sample request:**
    ```json
    {
      "doctor_id": 3,
      "clinic_id": 1,
      "start_time": "2026-03-20T09:00:00",
      "end_time":   "2026-03-20T09:30:00",
      "capacity": 1,
      "status": "available"
    }
    ```
    """
    return await SlotService(db).create(payload)


@router.get("", response_model=List[SlotResponse])
async def list_slots(
    doctor_id: Optional[int] = Query(None),
    clinic_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None, description="Filter slots starting at or after this datetime"),
    date_to: Optional[datetime] = Query(None, description="Filter slots starting at or before this datetime"),
    status: Optional[SlotStatus] = Query(None, description="Filter by slot status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_all: bool = Query(False, description="Include booked / past slots"),
    db: AsyncSession = Depends(get_db),
):
    """List slots with optional filters.

    - By default returns only **available**, **active**, **future** slots.
    - Set ``include_all=true`` to also return booked/past slots.
    - Use ``status`` to filter by a specific slot status.
    """
    return await SlotService(db).list_available(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        skip=skip,
        limit=limit,
        include_all=include_all,
    )


@router.put("/{slot_id}", response_model=SlotResponse)
async def update_slot(
    slot_id: int,
    payload: SlotUpdate,
    force: bool = Query(False, description="Allow editing a booked slot (admin override)"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "super_admin")),
):
    """Admin / Super-Admin: update a slot's time, capacity, or status.

    Booked slots (booked_count > 0) cannot have their time or capacity changed
    unless ``force=true`` is supplied.

    **Sample request – reschedule a slot:**
    ```json
    {
      "start_time": "2026-03-20T10:00:00",
      "end_time":   "2026-03-20T10:30:00"
    }
    ```

    **Sample request – block a slot:**
    ```json
    { "status": "blocked" }
    ```

    **Sample request – cancel a slot:**
    ```json
    { "status": "cancelled" }
    ```
    """
    return await SlotService(db).update(slot_id, payload, force=force)


@router.patch("/{slot_id}/toggle-active", response_model=SlotToggleResponse)
async def toggle_slot_active(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "super_admin")),
):
    """Admin / Super-Admin: toggle a slot's active/inactive state.

    - **Active → Inactive**: hides the slot from the public listing (soft disable).
    - **Inactive → Active**: makes the slot visible again.

    Slots with active bookings cannot be deactivated.

    **Sample response:**
    ```json
    {
      "id": 7,
      "is_active": false,
      "message": "Slot 7 has been deactivated."
    }
    ```
    """
    return await SlotService(db).toggle_active(slot_id)


@router.delete("/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "super_admin")),
):
    """Admin / Super-Admin: soft-delete a slot (sets is_active=False).

    Slots with active bookings cannot be deleted.
    """
    await SlotService(db).delete(slot_id)

