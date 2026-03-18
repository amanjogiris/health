"""Slot routes."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.appointment import SlotStatus
from app.models.user import User, UserRole
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.slot_repository import SlotRepository
from app.schemas.slot_schema import SlotCreate, SlotResponse, SlotToggleResponse, SlotUpdate
from app.services.slot_service import SlotService

router = APIRouter(prefix="/slots", tags=["Slots"])


# ── shared auth helpers ───────────────────────────────────────────────────────

async def _require_admin_or_doctor(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow admin, super_admin, and doctor roles. Others get 403."""
    role = (current_user.role.value if hasattr(current_user.role, "value") else current_user.role or "").lower()
    if role not in {"admin", "super_admin", "doctor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    return current_user


async def _resolve_doctor_id(
    current_user: User = Depends(_require_admin_or_doctor),
    db: AsyncSession = Depends(get_db),
) -> Optional[int]:
    """Return the doctor_id for the current user if they are a doctor, else None."""
    role = (current_user.role.value if hasattr(current_user.role, "value") else current_user.role or "").lower()
    if role == "doctor":
        doctor = await DoctorRepository(db).get_by_user_id(current_user.id)
        if doctor is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found for this user.",
            )
        return doctor.id
    return None  # admin / super_admin – no ownership restriction


async def _assert_slot_ownership(
    slot_id: int,
    owner_doctor_id: Optional[int],
    db: AsyncSession,
) -> None:
    """If owner_doctor_id is set (doctor role), verify the slot belongs to them."""
    if owner_doctor_id is None:
        return
    slot = await SlotRepository(db).get_by_id(slot_id)
    if slot is None:
        return  # service layer will raise NotFound
    if slot.doctor_id != owner_doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own slots.",
        )


# ── routes ────────────────────────────────────────────────────────────────────

@router.post("", response_model=SlotResponse, status_code=201)
async def create_slot(
    payload: SlotCreate,
    db: AsyncSession = Depends(get_db),
    owner_doctor_id: Optional[int] = Depends(_resolve_doctor_id),
):
    """Admin / Super-Admin / Doctor: create a single appointment slot.

    Doctors may only create slots for themselves – the ``doctor_id`` in the
    payload must match their own profile.

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
    if owner_doctor_id is not None and payload.doctor_id != owner_doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create slots for your own doctor profile.",
        )
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
    owner_doctor_id: Optional[int] = Depends(_resolve_doctor_id),
):
    """Admin / Super-Admin / Doctor: update a slot's time, capacity, or status.

    Doctors may only update their own slots. Booked slots cannot have their
    time or capacity changed unless ``force=true`` is supplied (admin only).
    """
    await _assert_slot_ownership(slot_id, owner_doctor_id, db)
    # Doctors cannot use force override
    if owner_doctor_id is not None:
        force = False
    return await SlotService(db).update(slot_id, payload, force=force)


@router.patch("/{slot_id}/toggle-active", response_model=SlotToggleResponse)
async def toggle_slot_active(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    owner_doctor_id: Optional[int] = Depends(_resolve_doctor_id),
):
    """Admin / Super-Admin / Doctor: toggle a slot's active/inactive state.

    Doctors may only toggle their own slots.
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
    await _assert_slot_ownership(slot_id, owner_doctor_id, db)
    return await SlotService(db).toggle_active(slot_id)


@router.delete("/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    owner_doctor_id: Optional[int] = Depends(_resolve_doctor_id),
):
    """Admin / Super-Admin / Doctor: soft-delete a slot (sets is_active=False).

    Doctors may only delete their own slots.
    Slots with active bookings cannot be deleted.
    """
    await _assert_slot_ownership(slot_id, owner_doctor_id, db)
    await SlotService(db).delete(slot_id)


