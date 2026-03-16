"""Doctor routes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role, require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.doctor_schema import (
    AvailabilityInput,
    AvailabilityResponse,
    AdminDoctorUpdate,
    DoctorCreate,
    DoctorRegister,
    DoctorResponse,
    DoctorUpdate,
)
from app.schemas.appointment_schema import AppointmentResponse
from app.schemas.pagination import PaginatedResponse
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["Doctors"])


# ── Public / all-authenticated ────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse[DoctorResponse])
async def list_doctors(
    specialty: Optional[str] = Query(None),
    clinic_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Public: anyone can browse doctors (returns doctor_name + clinic_name)."""
    return await DoctorService(db).list_all(specialty=specialty, clinic_id=clinic_id, skip=skip, limit=limit, search=search)


@router.get("/profile", response_model=DoctorResponse)
async def get_own_doctor_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["DOCTOR"])),
):
    """Doctor: view own profile."""
    return await DoctorService(db).get_profile_by_user(current_user.id)


@router.put("/profile", response_model=DoctorResponse)
async def update_own_doctor_profile(
    payload: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["DOCTOR"])),
):
    """Doctor: update own profile."""
    return await DoctorService(db).update_profile_by_user(current_user.id, payload)


@router.get("/appointments", response_model=List[AppointmentResponse])
async def get_own_doctor_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["DOCTOR"])),
):
    """Doctor: view own appointments."""
    return await DoctorService(db).get_appointments_by_user(current_user.id, skip, limit)


@router.get("/{doctor_id}/availability", response_model=List[AvailabilityResponse])
async def get_doctor_availability(doctor_id: int, db: AsyncSession = Depends(get_db)):
    """Public: get weekly availability for a doctor."""
    return await DoctorService(db).get_availability(doctor_id)


@router.post("/{doctor_id}/slots/generate", status_code=200)
async def generate_doctor_slots(
    doctor_id: int,
    days_ahead: int = Query(60, ge=1, le=365, description="How many days ahead to generate slots for"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: generate (or fill gaps in) appointment slots for a doctor.

    Uses the doctor\u2019s stored weekly availability.  Idempotent \u2013 already-existing
    slots at the same start_time are skipped.  Set *days_ahead* up to 365 to
    cover as many weeks into the future as needed.
    """
    count = await DoctorService(db).generate_slots_for_doctor(doctor_id, days_ahead)
    return {"generated": count, "days_ahead": days_ahead}


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    """Public: get doctor by ID (includes availability)."""
    return await DoctorService(db).get(doctor_id)


# ── Admin-only management ─────────────────────────────────────────────────────

@router.put("/{doctor_id}/availability", response_model=List[AvailabilityResponse])
async def set_doctor_availability(
    doctor_id: int,
    availability: List[AvailabilityInput],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: replace weekly availability and regenerate slots."""
    return await DoctorService(db).set_availability(doctor_id, availability)


@router.post("/register", response_model=DoctorResponse, status_code=201)
async def register_doctor(
    payload: DoctorRegister,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: create a user account + doctor profile + slots in one step."""
    return await DoctorService(db).register_with_user(payload)


@router.post("", response_model=DoctorResponse, status_code=201)
async def create_doctor(
    payload: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: create a doctor record from an existing user_id."""
    return await DoctorService(db).create(payload)


@router.put("/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: int,
    payload: AdminDoctorUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: full update (user fields + doctor profile)."""
    return await DoctorService(db).admin_full_update(doctor_id, payload)


@router.delete("/{doctor_id}", status_code=204)
async def delete_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"])),
):
    """Super-Admin: permanently remove a doctor record."""
    await DoctorService(db).delete(doctor_id)

