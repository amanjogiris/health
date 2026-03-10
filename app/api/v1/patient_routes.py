"""Patient routes."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.patient_schema import PatientUpdate, PatientResponse, AdminPatientUpdate
from app.schemas.appointment_schema import AppointmentResponse
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("", response_model=List[PatientResponse])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: list all patients."""
    return await PatientService(db).list_all(skip, limit)


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
    payload: AdminPatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT", "ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: full update (user + profile). Patient: own profile-only fields."""
    is_admin = current_user.role.value in ("admin", "super_admin")
    if is_admin:
        return await PatientService(db).admin_full_update(patient_id, payload)
    # Patient can only update their own medical profile fields
    patient_payload = PatientUpdate(
        date_of_birth=payload.date_of_birth,
        blood_group=payload.blood_group,
        allergies=payload.allergies,
        emergency_contact=payload.emergency_contact,
    )
    return await PatientService(db).update_with_ownership_check(patient_id, patient_payload, current_user)


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: deactivate a patient."""
    await PatientService(db).deactivate(patient_id)


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
