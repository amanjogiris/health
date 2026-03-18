"""Leave management routes.

Endpoints:
    POST   /doctors/{doctor_id}/leaves              – create a leave block
    GET    /doctors/{doctor_id}/leaves              – list leave blocks
    DELETE /doctors/{doctor_id}/leaves/{leave_id}   – remove a leave block

Authorization:
    - Admin / super_admin: full access to any doctor.
    - Doctor: can only manage their own leave records.
"""
from __future__ import annotations

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor_leave_schema import DoctorLeaveCreate, DoctorLeaveResponse
from app.services.doctor_leave_service import DoctorLeaveService

router = APIRouter(tags=["Doctor Leaves"])


# ── shared dependency ─────────────────────────────────────────────────────────

async def _get_own_doctor_id(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Optional[int]:
    """Return the Doctor.id for the currently logged-in *doctor* user, or None."""
    role = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else current_user.role or ""
    ).lower()
    if role != "doctor":
        return None
    repo = DoctorRepository(db)
    doctor = await repo.get_by_user_id(current_user.id)
    return doctor.id if doctor else None


# ── routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/doctors/{doctor_id}/leaves",
    response_model=DoctorLeaveResponse,
    status_code=201,
    summary="Create a leave / unavailability block for a doctor",
)
async def create_leave(
    doctor_id: int,
    payload: DoctorLeaveCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    own_doctor_id: Optional[int] = Depends(_get_own_doctor_id),
) -> DoctorLeaveResponse:
    role = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else current_user.role or ""
    )
    svc = DoctorLeaveService(db)
    return await svc.create_leave(
        doctor_id=doctor_id,
        payload=payload,
        requesting_user_id=current_user.id,
        requesting_user_role=role,
        own_doctor_id=own_doctor_id,
    )


@router.get(
    "/doctors/{doctor_id}/leaves",
    response_model=List[DoctorLeaveResponse],
    summary="List leave / unavailability blocks for a doctor",
)
async def list_leaves(
    doctor_id: int,
    date_from: Optional[datetime.date] = Query(None, description="Filter from date (inclusive)"),
    date_to: Optional[datetime.date] = Query(None, description="Filter to date (inclusive)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    own_doctor_id: Optional[int] = Depends(_get_own_doctor_id),
) -> List[DoctorLeaveResponse]:
    role = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else current_user.role or ""
    )
    svc = DoctorLeaveService(db)
    return await svc.list_leaves(
        doctor_id=doctor_id,
        date_from=date_from,
        date_to=date_to,
        requesting_user_role=role,
        own_doctor_id=own_doctor_id,
    )


@router.delete(
    "/doctors/{doctor_id}/leaves/{leave_id}",
    status_code=204,
    summary="Delete a leave / unavailability block",
)
async def delete_leave(
    doctor_id: int,
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    own_doctor_id: Optional[int] = Depends(_get_own_doctor_id),
) -> None:
    role = (
        current_user.role.value
        if hasattr(current_user.role, "value")
        else current_user.role or ""
    )
    svc = DoctorLeaveService(db)
    await svc.delete_leave(
        doctor_id=doctor_id,
        leave_id=leave_id,
        requesting_user_role=role,
        own_doctor_id=own_doctor_id,
    )


__all__ = ["router"]
