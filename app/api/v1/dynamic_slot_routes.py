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
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
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
    return await DynamicSlotService(db).book(payload)


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
        from app.utils.exceptions import ForbiddenError
        raise ForbiddenError("You are not authorised to view this appointment.")

    # Resolve interval for slots_count
    service = DynamicSlotService(db)
    interval = await service._get_interval_for_appointment(appt)
    return DynamicAppointmentResponse.from_orm_with_interval(appt, interval)
