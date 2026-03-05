"""Patient routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.patient_schema import PatientUpdate, PatientResponse
from app.schemas.appointment_schema import AppointmentResponse
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT", "ADMIN", "SUPER_ADMIN"])),
):
    """Patient (own) / Admin: view patient profile."""
    return await PatientService(db).get_with_ownership_check(patient_id, current_user)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT"])),
):
    """Patient: update own profile only."""
    return await PatientService(db).update(patient_id, payload, current_user)


@router.get("/{patient_id}/appointments", response_model=List[AppointmentResponse])
async def patient_appointments(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT", "ADMIN", "SUPER_ADMIN"])),
):
    """Patient (own) / Admin: list patient appointments."""
    return await PatientService(db).get_appointments(patient_id, skip, limit)
