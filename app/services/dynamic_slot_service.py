"""Dynamic Slot Service – orchestrates the Factory Method pattern.

Responsibilities:
    1. Fetch the doctor's availability record for the requested date.
    2. Fetch all existing bookings for that day.
    3. Instantiate the correct ``SlotFactory`` (currently always
       ``FixedIntervalSlotFactory``).
    4. Delegate slot generation to the factory.
    5. Handle atomic booking with race-condition protection.

Design note
-----------
The service layer is the *only* place that knows which factory to use.
Adding a new strategy (e.g. ``VariableDurationSlotFactory``) requires only a
new factory class + a small branch here; no API or repository changes needed.
"""
from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.factories.fixed_interval import FixedIntervalSlotFactory
from app.models.appointment import SlotStatus
from app.models.doctor import DoctorAvailability
from app.repositories.availability_repository import AvailabilityRepository
from app.repositories.doctor_leave_repository import DoctorLeaveRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.dynamic_appointment_repository import DynamicAppointmentRepository
from app.repositories.slot_repository import SlotRepository
from app.schemas.dynamic_slot_schema import (
    DoctorSlotsResponse,
    DynamicAppointmentResponse,
    DynamicBookRequest,
    DynamicSlotResponse,
)
from app.utils.exceptions import BusinessRuleError, ForbiddenError, NotFoundError


class DynamicSlotService:
    """Service layer for factory-driven slot generation and dynamic booking."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._appt_repo = DynamicAppointmentRepository(db)
        self._avail_repo = AvailabilityRepository(db)
        self._doctor_repo = DoctorRepository(db)
        self._leave_repo = DoctorLeaveRepository(db)
        self._slot_repo = SlotRepository(db)

    # ── Slot generation ───────────────────────────────────────────────────────

    async def get_slots_for_date(
        self,
        doctor_id: int,
        date: datetime.date,
        only_available: bool = False,
    ) -> DoctorSlotsResponse:
        """Generate and return all slots for *doctor_id* on *date*.

        Steps:
            1. Verify doctor exists.
            2. Look up availability rule matching the day-of-week.
            3. Fetch existing bookings → booked windows.
            4. Call ``FixedIntervalSlotFactory.generate_slots()``.
            5. Return rich response.

        Args:
            doctor_id:      Primary key of the doctor.
            date:           Calendar date to generate slots for.
            only_available: When True, filter out already-booked slots from the
                            response (useful for patient-facing booking UIs).

        Raises:
            NotFoundError:      Doctor not found.
            BusinessRuleError:  Doctor has no availability set for that weekday.
        """
        # 1. Verify doctor
        doctor = await self._doctor_repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")

        # 2. Availability for this day-of-week (0=Mon … 6=Sun)
        day_of_week = date.weekday()
        availability = await self._get_availability_for_day(doctor_id, day_of_week)

        # 2b. Manual (one-off) slots created by the doctor for this specific date
        manual_slots = await self._slot_repo.get_active_slots_for_date(doctor_id, date)

        if availability is None and not manual_slots:
            raise BusinessRuleError(
                f"Doctor {doctor_id} has no availability configured for "
                f"{date.strftime('%A')} (day_of_week={day_of_week})."
            )

        # ── Case A: no recurring schedule → build response from manual slots only ──
        if availability is None:
            slot_responses = [
                DynamicSlotResponse(
                    start_time=_ensure_utc(s.start_time),
                    end_time=_ensure_utc(s.end_time),
                    is_available=(
                        s.status == SlotStatus.AVAILABLE
                        and s.booked_count < s.capacity
                    ),
                    duration_minutes=int(
                        (_ensure_utc(s.end_time) - _ensure_utc(s.start_time)).total_seconds() // 60
                    ),
                )
                for s in manual_slots
            ]
            if only_available:
                slot_responses = [s for s in slot_responses if s.is_available]
            first_duration = slot_responses[0].duration_minutes if slot_responses else 0
            return DoctorSlotsResponse(
                doctor_id=doctor_id,
                date=date,
                slot_interval_minutes=first_duration,
                total_slots=len(slot_responses),
                available_slots=sum(1 for s in slot_responses if s.is_available),
                slots=slot_responses,
            )

        # ── Case B: recurring schedule exists → generate schedule slots ──

        # 3. Existing bookings → (start, end) pairs
        booked_windows = await self._appt_repo.get_booked_windows_for_date(
            doctor_id, date
        )

        # 4. Factory – pick algorithm based on availability's slot_interval
        interval = getattr(availability, "slot_interval", None) or 15
        factory = FixedIntervalSlotFactory(interval_minutes=interval)

        window_start = datetime.datetime.combine(
            date, availability.start_time, tzinfo=datetime.timezone.utc
        )
        window_end = datetime.datetime.combine(
            date, availability.end_time, tzinfo=datetime.timezone.utc
        )

        # 4b. Doctor leave windows → merge into blocked windows
        leave_windows = await self._get_leave_windows_for_date(
            doctor_id, date, window_start, window_end
        )
        all_blocked = booked_windows + leave_windows

        raw_slots = factory.generate_slots(window_start, window_end, all_blocked)

        # 4c. Merge manual slots that fall OUTSIDE the schedule window
        schedule_start = _ensure_utc(datetime.datetime.combine(
            date, availability.start_time, tzinfo=datetime.timezone.utc
        ))
        schedule_end = _ensure_utc(datetime.datetime.combine(
            date, availability.end_time, tzinfo=datetime.timezone.utc
        ))
        extra_manual: List[DynamicSlotResponse] = []
        for s in manual_slots:
            s_start = _ensure_utc(s.start_time)
            s_end = _ensure_utc(s.end_time)
            # Include manual slot only if it doesn't overlap the generated schedule window
            if s_end <= schedule_start or s_start >= schedule_end:
                extra_manual.append(
                    DynamicSlotResponse(
                        start_time=s_start,
                        end_time=s_end,
                        is_available=(
                            s.status == SlotStatus.AVAILABLE
                            and s.booked_count < s.capacity
                        ),
                        duration_minutes=int(
                            (s_end - s_start).total_seconds() // 60
                        ),
                    )
                )

        # 5. Build response
        if only_available:
            raw_slots = [s for s in raw_slots if s.is_available]

        slot_responses = [DynamicSlotResponse.from_dynamic_slot(s) for s in raw_slots]
        slot_responses = sorted(
            slot_responses + extra_manual, key=lambda x: x.start_time
        )

        return DoctorSlotsResponse(
            doctor_id=doctor_id,
            date=date,
            slot_interval_minutes=interval,
            total_slots=len(slot_responses),
            available_slots=sum(1 for s in slot_responses if s.is_available),
            slots=slot_responses,
        )

    # ── Booking ───────────────────────────────────────────────────────────────

    async def book(self, payload: DynamicBookRequest) -> DynamicAppointmentResponse:
        """Atomically book a (multi-)slot block.

        Algorithm:
            1. Validate doctor + availability exists for the requested date.
            2. Compute the booking end_time from slots_requested × interval.
            3. Verify the block is still available (application-level check).
            4. Flush to DB – the UNIQUE constraint on (doctor_id, start_time)
               catches any concurrent race condition at the DB level.
            5. Commit and return the persisted appointment.

        Raises:
            NotFoundError:       Doctor not found.
            BusinessRuleError:   Slot unavailable / conflict detected.
        """
        try:
            doctor = await self._doctor_repo.get_by_id(payload.doctor_id)
            if doctor is None:
                raise NotFoundError("Doctor")

            # Ensure timezone-awareness
            start_time = _ensure_utc(payload.start_time)
            date = start_time.date()
            day_of_week = date.weekday()

            availability = await self._get_availability_for_day(
                payload.doctor_id, day_of_week
            )
            if availability is None:
                raise BusinessRuleError(
                    f"Doctor {payload.doctor_id} has no availability for "
                    f"{date.strftime('%A')}."
                )

            interval = getattr(availability, "slot_interval", None) or 15
            factory = FixedIntervalSlotFactory(interval_minutes=interval)

            # Compute booking window
            end_time = factory.block_end_time(start_time, payload.slots_requested)

            # Validate that start_time falls inside the availability window
            window_start = datetime.datetime.combine(
                date, availability.start_time, tzinfo=datetime.timezone.utc
            )
            window_end = datetime.datetime.combine(
                date, availability.end_time, tzinfo=datetime.timezone.utc
            )
            if start_time < window_start or end_time > window_end:
                raise BusinessRuleError(
                    "The requested time slot falls outside the doctor's availability window "
                    f"({availability.start_time.strftime('%H:%M')} – "
                    f"{availability.end_time.strftime('%H:%M')})."
                )

            # Leave window check – reject if doctor is on leave
            leave_windows = await self._get_leave_windows_for_date(
                payload.doctor_id, date, window_start, window_end
            )
            for lw_start, lw_end in leave_windows:
                if not (end_time <= lw_start or start_time >= lw_end):
                    raise BusinessRuleError(
                        "The doctor is on leave during the requested time. "
                        "Please choose a different date or time."
                    )

            # Application-level conflict check (before acquiring DB lock)
            existing_windows = await self._appt_repo.get_booked_windows_for_date(
                payload.doctor_id, date
            )
            if not factory.is_block_available(start_time, existing_windows, payload.slots_requested):
                raise BusinessRuleError(
                    "The selected slot is already booked or overlaps an existing appointment."
                )

            # Persist – flush triggers the DB unique constraint (race-condition guard)
            appt = await self._appt_repo.create(
                doctor_id=payload.doctor_id,
                patient_id=payload.patient_id,
                clinic_id=payload.clinic_id,
                start_time=start_time,
                end_time=end_time,
                reason_for_visit=payload.reason_for_visit,
            )
            await self.db.commit()
            await self.db.refresh(appt)

        except IntegrityError:
            await self.db.rollback()
            raise BusinessRuleError(
                "The selected slot was just booked by another request. Please choose another time."
            )
        except Exception:
            await self.db.rollback()
            raise

        return DynamicAppointmentResponse.from_orm_with_interval(appt, interval)

    async def cancel(
        self,
        appt_id: int,
        reason: str,
        requesting_user_id: int,
        is_admin: bool = False,
    ) -> DynamicAppointmentResponse:
        """Cancel a dynamic appointment.

        Patients may only cancel their own appointments; admins can cancel any.
        """
        appt = await self._appt_repo.get_by_id(appt_id)
        if appt is None:
            raise NotFoundError("DynamicAppointment")

        if not is_admin and appt.patient_id != requesting_user_id:
            raise ForbiddenError("You are not authorised to cancel this appointment.")

        if appt.status.value == "cancelled":
            raise BusinessRuleError("Appointment is already cancelled.")

        cancelled = await self._appt_repo.cancel(appt_id, reason)
        if cancelled is None:
            raise NotFoundError("DynamicAppointment")

        # Determine interval for slots_count computation
        interval = await self._get_interval_for_appointment(cancelled)
        return DynamicAppointmentResponse.from_orm_with_interval(cancelled, interval)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_availability_for_day(
        self,
        doctor_id: int,
        day_of_week: int,
    ) -> Optional[DoctorAvailability]:
        """Return the first availability rule matching *day_of_week*, or None."""
        all_avail = await self._avail_repo.get_by_doctor(doctor_id)
        for avail in all_avail:
            if avail.day_of_week == day_of_week:
                return avail
        return None

    async def _get_interval_for_appointment(
        self, appt: object
    ) -> int:
        """Resolve the slot_interval from the doctor's availability (fallback 15)."""
        day_of_week = appt.start_time.weekday()  # type: ignore[attr-defined]
        avail = await self._get_availability_for_day(
            appt.doctor_id, day_of_week  # type: ignore[attr-defined]
        )
        return (getattr(avail, "slot_interval", None) or 15) if avail else 15

    async def _get_leave_windows_for_date(
        self,
        doctor_id: int,
        date: datetime.date,
        avail_start: datetime.datetime,
        avail_end: datetime.datetime,
    ) -> List[tuple]:
        """Return a list of (start, end) UTC datetime tuples representing leave blocks.

        Full-day leave maps to the full availability window; partial leave uses
        the specified start/end times combined with the requested date.
        """
        leaves = await self._leave_repo.get_by_doctor_and_date(doctor_id, date)
        windows: List[tuple] = []
        for leave in leaves:
            if leave.is_full_day:
                windows.append((avail_start, avail_end))
            else:
                if leave.start_time and leave.end_time:
                    lw_start = datetime.datetime.combine(
                        date, leave.start_time, tzinfo=datetime.timezone.utc
                    )
                    lw_end = datetime.datetime.combine(
                        date, leave.end_time, tzinfo=datetime.timezone.utc
                    )
                    windows.append((lw_start, lw_end))
        return windows


# ── Timezone helper ───────────────────────────────────────────────────────────

def _ensure_utc(dt: datetime.datetime) -> datetime.datetime:
    """Attach UTC timezone if the datetime is naive."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)
