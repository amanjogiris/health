"""Service layer for doctor leave / unavailability management."""
from __future__ import annotations

import datetime
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.repositories.doctor_leave_repository import DoctorLeaveRepository
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor_leave_schema import DoctorLeaveCreate, DoctorLeaveResponse


class DoctorLeaveService:
    """Manage leave / unavailability blocks for doctors.

    Business rules:
    - A doctor can create a leave for themselves.
    - An admin / super_admin can create a leave for any doctor.
    - A partial-day leave must have start_time < end_time (validated in schema).
    - A leave date cannot be in the past (doctors cannot retroactively block).
    - Deletion is allowed by the owning doctor or any admin.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._repo = DoctorLeaveRepository(db)
        self._doctor_repo = DoctorRepository(db)

    async def create_leave(
        self,
        doctor_id: int,
        payload: DoctorLeaveCreate,
        requesting_user_id: int,
        requesting_user_role: str,
        own_doctor_id: Optional[int] = None,
    ) -> DoctorLeaveResponse:
        """Create a leave record for *doctor_id*.

        Raises:
            NotFoundError:      Doctor not found.
            ForbiddenError:     Non-admin trying to create leave for another doctor.
        """
        # Verify doctor exists
        doctor = await self._doctor_repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")

        role = requesting_user_role.lower()
        is_admin = role in {"admin", "super_admin"}

        # Non-admins (doctors) may only post for their own profile
        if not is_admin:
            if own_doctor_id is None or own_doctor_id != doctor_id:
                raise ForbiddenError(
                    "Doctors may only create leave records for their own profile."
                )

        leave = await self._repo.create(
            doctor_id=doctor_id,
            date=payload.date,
            is_full_day=payload.is_full_day,
            start_time=payload.start_time,
            end_time=payload.end_time,
            reason=payload.reason,
        )
        await self.db.commit()
        await self.db.refresh(leave)
        return DoctorLeaveResponse.model_validate(leave)

    async def list_leaves(
        self,
        doctor_id: int,
        date_from: Optional[datetime.date] = None,
        date_to: Optional[datetime.date] = None,
        requesting_user_role: str = "",
        own_doctor_id: Optional[int] = None,
    ) -> List[DoctorLeaveResponse]:
        """List all leave records for *doctor_id*.

        Raises:
            NotFoundError:  Doctor not found.
            ForbiddenError: Non-admin trying to list another doctor's leaves.
        """
        doctor = await self._doctor_repo.get_by_id(doctor_id)
        if doctor is None:
            raise NotFoundError("Doctor")

        role = requesting_user_role.lower()
        is_admin = role in {"admin", "super_admin"}

        if not is_admin and (own_doctor_id is None or own_doctor_id != doctor_id):
            raise ForbiddenError("Doctors may only view their own leave records.")

        leaves = await self._repo.get_by_doctor(doctor_id, date_from, date_to)
        return [DoctorLeaveResponse.model_validate(l) for l in leaves]

    async def delete_leave(
        self,
        doctor_id: int,
        leave_id: int,
        requesting_user_role: str,
        own_doctor_id: Optional[int] = None,
    ) -> None:
        """Delete a leave record.

        Raises:
            NotFoundError:  Leave not found or belongs to a different doctor.
            ForbiddenError: Non-admin trying to delete another doctor's leave.
        """
        leave = await self._repo.get_by_id(leave_id)
        if leave is None or leave.doctor_id != doctor_id:
            raise NotFoundError("DoctorLeave")

        role = requesting_user_role.lower()
        is_admin = role in {"admin", "super_admin"}

        if not is_admin and (own_doctor_id is None or own_doctor_id != doctor_id):
            raise ForbiddenError("Doctors may only delete their own leave records.")

        await self._repo.delete(leave_id)
        await self.db.commit()


__all__ = ["DoctorLeaveService"]
