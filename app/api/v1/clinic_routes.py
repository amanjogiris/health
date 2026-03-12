"""Clinic routes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.clinic_schema import ClinicCreate, ClinicUpdate, ClinicResponse
from app.schemas.doctor_schema import DoctorResponse
from app.schemas.pagination import PaginatedResponse
from app.services.clinic_service import ClinicService

router = APIRouter(prefix="/clinics", tags=["Clinics"])


@router.get("", response_model=PaginatedResponse[ClinicResponse])
async def list_clinics(
    city: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Public: anyone can list clinics."""
    return await ClinicService(db).list_all(city=city, skip=skip, limit=limit, search=search)


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(clinic_id: int, db: AsyncSession = Depends(get_db)):
    """Public: get clinic by ID."""
    return await ClinicService(db).get(clinic_id)


@router.get("/{clinic_id}/doctors", response_model=List[DoctorResponse])
async def clinic_doctors(clinic_id: int, db: AsyncSession = Depends(get_db)):
    """Public: list doctors for a clinic."""
    return await ClinicService(db).get_doctors(clinic_id)


@router.post("", response_model=ClinicResponse, status_code=201)
async def create_clinic(
    payload: ClinicCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: create a new clinic."""
    return await ClinicService(db).create(payload)


@router.put("/{clinic_id}", response_model=ClinicResponse)
async def update_clinic(
    clinic_id: int,
    payload: ClinicUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: update clinic details."""
    return await ClinicService(db).update(clinic_id, payload)


@router.delete("/{clinic_id}", status_code=204)
async def delete_clinic(
    clinic_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"])),
):
    """Super-Admin only: soft-delete a clinic."""
    await ClinicService(db).delete(clinic_id)
