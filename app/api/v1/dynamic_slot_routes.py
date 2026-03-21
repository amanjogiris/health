"""Dynamic slot & appointment routes.

Endpoints
---------
GET  /api/v1/doctors/{doctor_id}/dynamic-slots
    → Return factory-generated slots for a doctor on a given date.

POST /api/v1/appointments/dynamic
    → Book a (multi-)slot block using the dynamic slot system.

POST /api/v1/appointments/dynamic/{appt_id}/cancel
    → Cancel a dynamic appointment.

GET  /api/v1/appointments/dynamic/{appt_id}
    → Retrieve a single dynamic appointment by ID.
"""
from __future__ import annotations

import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_role, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.dynamic_slot_schema import (
    DoctorSlotsResponse,
    DynamicAppointmentResponse,
    DynamicBookRequest,
    DynamicCancelRequest,
)
from app.services.dynamic_slot_service import DynamicSlotService
from app.utils.exceptions import NotFoundError

# ── Router objects ─────────────────────────────────────────────────────────────

# Slots are nested under /doctors to make the URL ergonomic.
doctor_dynamic_router = APIRouter(prefix="/doctors", tags=["Dynamic Slots"])

# Appointment actions live under /appointments/dynamic.
appt_dynamic_router = APIRouter(prefix="/appointments/dynamic", tags=["Dynamic Appointments"])


# ── Slot endpoint ──────────────────────────────────────────────────────────────

@doctor_dynamic_router.get(
    "/{doctor_id}/dynamic-slots",
    response_model=DoctorSlotsResponse,
    summary="Get factory-generated slots for a doctor on a date",
)
async def get_dynamic_slots(
    doctor_id: int,
    date: datetime.date = Query(..., description="Calendar date (YYYY-MM-DD)"),
    only_available: bool = Query(
        False, description="When true, only available (unbooked) slots are returned"
    ),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint – no authentication required.

    Returns a list of **dynamically generated** time slots based on the
    doctor's stored availability for the given weekday.  Slots that overlap
    existing bookings are included in the response with ``is_available=false``
    unless ``only_available=true`` is set.

    **Example:**
    ```
    GET /api/v1/doctors/3/dynamic-slots?date=2026-03-20
    GET /api/v1/doctors/3/dynamic-slots?date=2026-03-20&only_available=true
    ```
    """
    return await DynamicSlotService(db).get_slots_for_date(
        doctor_id=doctor_id,
        date=date,
        only_available=only_available,
    )


# ── Appointment endpoints ──────────────────────────────────────────────────────

@appt_dynamic_router.post(
    "",
    response_model=DynamicAppointmentResponse,
    status_code=201,
    summary="Book a dynamic slot",
)
async def book_dynamic_slot(
    payload: DynamicBookRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book a factory-generated slot.

    - Patients may book any available slot.
    - Set ``slots_requested > 1`` for a multi-slot (extended duration) booking
      (e.g. ``slots_requested=2`` with a 15-minute interval books a 30-minute block).
    - The server rejects bookings that conflict with an existing appointment.
    - Concurrent duplicate bookings are blocked by a database unique constraint.

    **Example (single slot):**
    ```json
    {
      "doctor_id": 3,
      "patient_id": 7,
      "clinic_id": 1,
      "start_time": "2026-03-20T09:00:00Z",
      "slots_requested": 1,
      "reason_for_visit": "Annual checkup"
    }
    ```

    **Example (multi-slot – 30 min with 15-min interval):**
    ```json
    {
      "doctor_id": 3,
      "patient_id": 7,
      "clinic_id": 1,
      "start_time": "2026-03-20T10:00:00Z",
      "slots_requested": 2
    }
    ```
    """
    # For PATIENT role: always resolve patient_id from the patients table using
    # the authenticated user's ID.  This prevents a patient from booking on behalf
    # of another patient by supplying a different patient_id in the payload.
    if current_user.role.value.lower() == "patient":
        from app.repositories.patient_repository import PatientRepository
        patient = await PatientRepository(db).get_by_user_id(current_user.id)
        if patient is None:
            from app.utils.exceptions import NotFoundError
            raise NotFoundError("Patient profile for current user")
        # Override payload with the real patients-table ID
        payload = payload.model_copy(update={"patient_id": patient.id})

    return await DynamicSlotService(db).book(payload)


@appt_dynamic_router.get(
    "",
    response_model=List[DynamicAppointmentResponse],
    summary="List all dynamic appointments (admin)",
)
async def list_dynamic_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
):
    """Admin / Super-Admin: list dynamic appointments across the system."""
    from app.repositories.dynamic_appointment_repository import (
        DynamicAppointmentRepository,
    )

    repo = DynamicAppointmentRepository(db)
    appts = await repo.list_all(skip=skip, limit=limit)

    service = DynamicSlotService(db)
    results = []
    for appt in appts:
        interval = await service._get_interval_for_appointment(appt)
        results.append(DynamicAppointmentResponse.from_orm_with_interval(appt, interval))
    return results


@appt_dynamic_router.get(
    "/patients/me",
    response_model=List[DynamicAppointmentResponse],
    summary="List logged-in patient's dynamic appointments",
)
async def list_my_dynamic_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000 ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["PATIENT"])),
):
    """Patient: list their own dynamic appointments."""
    import logging
    logger = logging.getLogger(__name__)
    
    from app.repositories.dynamic_appointment_repository import (
        DynamicAppointmentRepository,
    )
    from app.repositories.patient_repository import PatientRepository

    logger.info(f"[DIAGNOSE] Fetching appointments for user_id={current_user.id}, role={current_user.role}")
    
    patient = await PatientRepository(db).get_by_user_id(current_user.id)
    if patient is None:
        logger.warning(f"[DIAGNOSE] No patient found for user_id={current_user.id}")
        # Patient record not found – return empty list (patient may not have completed profile setup)
        return []

    logger.info(f"[DIAGNOSE] Found patient id={patient.id} for user_id={current_user.id}")

    repo = DynamicAppointmentRepository(db)
    appts = await repo.list_by_patient(patient.id, skip=skip, limit=limit)
    
    logger.info(f"[DIAGNOSE] Found {len(appts)} dynamic appointments for patient_id={patient.id}")
    
    # Resolve intervals
    service = DynamicSlotService(db)
    results = []
    for appt in appts:
        interval = await service._get_interval_for_appointment(appt)
        results.append(DynamicAppointmentResponse.from_orm_with_interval(appt, interval))
    
    logger.info(f"[DIAGNOSE] Returning {len(results)} mapped appointments")
    return results


@appt_dynamic_router.get(
    "/doctors/me",
    response_model=List[DynamicAppointmentResponse],
    summary="List logged-in doctor's dynamic appointments",
)
async def list_my_doctor_dynamic_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["DOCTOR"])),
):
    """Doctor: list their own dynamic appointments."""
    from app.repositories.dynamic_appointment_repository import (
        DynamicAppointmentRepository,
    )
    from app.repositories.doctor_repository import DoctorRepository

    doctor = await DoctorRepository(db).get_by_user_id(current_user.id)
    if not doctor:
        raise NotFoundError("Doctor profile")

    repo = DynamicAppointmentRepository(db)
    appts = await repo.list_by_doctor(doctor.id, skip=skip, limit=limit)

    # Batch-resolve patient names (patient_id may be Patient.id or User.id)
    from sqlalchemy import select as sa_select
    from app.models.patient import Patient
    from app.models.user import User as UserModel
    patient_ids = list({a.patient_id for a in appts})
    user_map: dict = {}
    if patient_ids:
        result = await db.execute(
            sa_select(Patient.id, UserModel.name)
            .join(UserModel, Patient.user_id == UserModel.id)
            .where(Patient.id.in_(patient_ids))
        )
        user_map = {pid: uname for pid, uname in result.all() if uname}
        unresolved = [pid for pid in patient_ids if pid not in user_map]
        if unresolved:
            fallback = await db.execute(
                sa_select(UserModel.id, UserModel.name).where(UserModel.id.in_(unresolved))
            )
            for uid, uname in fallback.all():
                if uname:
                    user_map[uid] = uname

    # Resolve intervals and attach patient names
    service = DynamicSlotService(db)
    results = []
    for appt in appts:
        interval = await service._get_interval_for_appointment(appt)
        resp = DynamicAppointmentResponse.from_orm_with_interval(appt, interval)
        resp.patient_name = user_map.get(appt.patient_id)
        results.append(resp)
    return results


@appt_dynamic_router.post(
    "/{appt_id}/cancel",
    response_model=DynamicAppointmentResponse,
    summary="Cancel a dynamic appointment",
)
async def cancel_dynamic_appointment(
    appt_id: int,
    payload: DynamicCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a dynamic appointment.

    - Patients may only cancel their **own** appointments.
    - Admins and super-admins may cancel any appointment.
    """
    is_admin = current_user.role.value.lower() in ("admin", "super_admin")
    return await DynamicSlotService(db).cancel(
        appt_id=appt_id,
        reason=payload.cancelled_reason,
        requesting_user_id=current_user.id,
        is_admin=is_admin,
    )


@appt_dynamic_router.get(
    "/{appt_id}",
    response_model=DynamicAppointmentResponse,
    summary="Get a single dynamic appointment",
)
async def get_dynamic_appointment(
    appt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a dynamic appointment by ID.

    Patients may only view their own appointments; admins can view any.
    """
    from app.repositories.dynamic_appointment_repository import (
        DynamicAppointmentRepository,
    )
    from app.services.dynamic_slot_service import _ensure_utc

    repo = DynamicAppointmentRepository(db)
    appt = await repo.get_by_id(appt_id)
    if appt is None:
        raise NotFoundError("DynamicAppointment")

    is_admin = current_user.role.value.lower() in ("admin", "super_admin")
    if not is_admin and appt.patient_id != current_user.id:
        # patient_id is the patients-table PK, not the user PK — resolve correctly.
        from app.repositories.patient_repository import PatientRepository
        patient = await PatientRepository(db).get_by_user_id(current_user.id)
        if patient is None or appt.patient_id != patient.id:
            from app.utils.exceptions import ForbiddenError
            raise ForbiddenError("You are not authorised to view this appointment.")

    # Resolve interval for slots_count
    service = DynamicSlotService(db)
    interval = await service._get_interval_for_appointment(appt)
    return DynamicAppointmentResponse.from_orm_with_interval(appt, interval)
