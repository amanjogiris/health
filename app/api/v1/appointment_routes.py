"""Appointment routes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.appointment_schema import AppointmentBook, AppointmentCancel, AppointmentResponse
from app.schemas.pagination import PaginatedResponse
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/book", response_model=AppointmentResponse, status_code=201)
async def book_appointment(
    payload: AppointmentBook,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT", "ADMIN", "SUPER_ADMIN"])),
):
    """Patient / Admin: book an appointment. Uses row-level locking to prevent double booking."""
    return await AppointmentService(db).book(payload)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: int,
    payload: AppointmentCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT", "DOCTOR", "ADMIN", "SUPER_ADMIN"])),
):
    """Patient / Doctor / Admin: cancel an appointment."""
    return await AppointmentService(db).cancel(appointment_id, payload, current_user)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT", "DOCTOR", "ADMIN", "SUPER_ADMIN"])),
):
    """Owner / Admin: view an appointment."""
    return await AppointmentService(db).get_with_ownership_check(appointment_id, current_user)


@router.get("", response_model=PaginatedResponse[AppointmentResponse])
async def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: list all appointments."""
    return await AppointmentService(db).list_all(skip=skip, limit=limit, search=search, status=status)
