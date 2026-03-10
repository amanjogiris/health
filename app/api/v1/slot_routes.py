"""Slot routes."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.slot_schema import SlotCreate, SlotResponse
from app.services.slot_service import SlotService

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.post("", response_model=SlotResponse, status_code=201)
async def create_slot(
    payload: SlotCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "super_admin")),
):
    """Admin / Super-Admin: create an appointment slot."""
    return await SlotService(db).create(payload)


@router.get("", response_model=List[SlotResponse])
async def list_slots(
    doctor_id: Optional[int] = Query(None),
    clinic_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    include_all: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await SlotService(db).list_available(
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
        include_all=include_all,
    )


@router.delete("/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin", "super_admin")),
):
    """Admin / Super-Admin: delete an appointment slot."""
    await SlotService(db).delete(slot_id)
