"""Repository layer for database operations."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.model import (
    User,
    Patient,
    Doctor,
    Clinic,
    AppointmentSlot,
    Appointment,
    UserRole,
    AppointmentStatus,
)


# ============================================================================
# User Repository
# ============================================================================


class UserRepository:
    """Repository for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(
        self, name: str, email: str, password: str, role: str = "patient", **kwargs
    ) -> User:
        """Create a new user."""
        user = User(
            name=name,
            email=email,
            role=UserRole(role),
            **kwargs,
        )
        user.set_password(password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_users(self, role: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with optional role filter."""
        stmt = select(User).where(User.is_active == True).offset(skip).limit(limit)

        if role:
            stmt = stmt.where(User.role == UserRole(role))

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_users_by_role(self, role: str) -> List[User]:
        """Get all users with a specific role."""
        stmt = select(User).where(User.role == UserRole(role), User.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()


# ============================================================================
# Patient Repository
# ============================================================================


class PatientRepository:
    """Repository for patient operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_patient(self, user_id: int, **kwargs) -> Patient:
        """Create a new patient."""
        patient = Patient(user_id=user_id, **kwargs)
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def get_patient_by_id(self, patient_id: int) -> Optional[Patient]:
        """Get patient by ID."""
        stmt = select(Patient).where(Patient.id == patient_id, Patient.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_patient_by_user_id(self, user_id: int) -> Optional[Patient]:
        """Get patient by user ID."""
        stmt = select(Patient).where(Patient.user_id == user_id, Patient.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_patient(self, patient_id: int, **kwargs) -> Optional[Patient]:
        """Update patient."""
        patient = await self.get_patient_by_id(patient_id)
        if not patient:
            return None

        for key, value in kwargs.items():
            if hasattr(patient, key) and value is not None:
                setattr(patient, key, value)

        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def list_patients(self, skip: int = 0, limit: int = 100) -> List[Patient]:
        """List all patients."""
        stmt = select(Patient).where(Patient.is_active == True).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()


# ============================================================================
# Clinic Repository
# ============================================================================


class ClinicRepository:
    """Repository for clinic operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_clinic(self, **kwargs) -> Clinic:
        """Create a new clinic."""
        clinic = Clinic(**kwargs)
        self.db.add(clinic)
        await self.db.commit()
        await self.db.refresh(clinic)
        return clinic

    async def get_clinic_by_id(self, clinic_id: int) -> Optional[Clinic]:
        """Get clinic by ID."""
        stmt = select(Clinic).where(Clinic.id == clinic_id, Clinic.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_clinic(self, clinic_id: int, **kwargs) -> Optional[Clinic]:
        """Update clinic."""
        clinic = await self.get_clinic_by_id(clinic_id)
        if not clinic:
            return None

        for key, value in kwargs.items():
            if hasattr(clinic, key) and value is not None:
                setattr(clinic, key, value)

        self.db.add(clinic)
        await self.db.commit()
        await self.db.refresh(clinic)
        return clinic

    async def list_clinics(self, skip: int = 0, limit: int = 100) -> List[Clinic]:
        """List all clinics."""
        stmt = select(Clinic).where(Clinic.is_active == True).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_clinics_by_city(self, city: str) -> List[Clinic]:
        """Get clinics by city."""
        stmt = select(Clinic).where(Clinic.city == city, Clinic.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()


# ============================================================================
# Doctor Repository
# ============================================================================


class DoctorRepository:
    """Repository for doctor operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_doctor(self, **kwargs) -> Doctor:
        """Create a new doctor."""
        doctor = Doctor(**kwargs)
        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor

    async def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """Get doctor by ID."""
        stmt = select(Doctor).where(Doctor.id == doctor_id, Doctor.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_doctor_by_user_id(self, user_id: int) -> Optional[Doctor]:
        """Get doctor by user ID."""
        stmt = select(Doctor).where(Doctor.user_id == user_id, Doctor.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_doctor(self, doctor_id: int, **kwargs) -> Optional[Doctor]:
        """Update doctor."""
        doctor = await self.get_doctor_by_id(doctor_id)
        if not doctor:
            return None

        for key, value in kwargs.items():
            if hasattr(doctor, key) and value is not None:
                setattr(doctor, key, value)

        self.db.add(doctor)
        await self.db.commit()
        await self.db.refresh(doctor)
        return doctor

    async def list_doctors(self, skip: int = 0, limit: int = 100) -> List[Doctor]:
        """List all doctors."""
        stmt = select(Doctor).where(Doctor.is_active == True).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_doctors_by_clinic(self, clinic_id: int) -> List[Doctor]:
        """Get doctors by clinic."""
        stmt = select(Doctor).where(Doctor.clinic_id == clinic_id, Doctor.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_doctors_by_specialty(self, specialty: str) -> List[Doctor]:
        """Get doctors by specialty."""
        stmt = select(Doctor).where(Doctor.specialty == specialty, Doctor.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def search_doctors(self, specialty: Optional[str] = None, clinic_id: Optional[int] = None) -> List[Doctor]:
        """Search doctors by criteria."""
        stmt = select(Doctor).where(Doctor.is_active == True)

        if specialty:
            stmt = stmt.where(Doctor.specialty == specialty)
        if clinic_id:
            stmt = stmt.where(Doctor.clinic_id == clinic_id)

        result = await self.db.execute(stmt)
        return result.scalars().all()


# ============================================================================
# Appointment Slot Repository
# ============================================================================


class AppointmentSlotRepository:
    """Repository for appointment slot operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_slot(self, **kwargs) -> AppointmentSlot:
        """Create a new appointment slot."""
        slot = AppointmentSlot(**kwargs)
        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot

    async def get_slot_by_id(self, slot_id: int) -> Optional[AppointmentSlot]:
        """Get slot by ID."""
        stmt = select(AppointmentSlot).where(AppointmentSlot.id == slot_id, AppointmentSlot.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_slot(self, slot_id: int, **kwargs) -> Optional[AppointmentSlot]:
        """Update slot."""
        slot = await self.get_slot_by_id(slot_id)
        if not slot:
            return None

        for key, value in kwargs.items():
            if hasattr(slot, key) and value is not None:
                setattr(slot, key, value)

        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot

    async def list_slots(self, skip: int = 0, limit: int = 100) -> List[AppointmentSlot]:
        """List all available slots."""
        stmt = (
            select(AppointmentSlot)
            .where(
                AppointmentSlot.is_active == True,
                AppointmentSlot.is_booked == False,
            )
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_doctor_slots(
        self, doctor_id: int, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> List[AppointmentSlot]:
        """Get slots for a doctor."""
        stmt = select(AppointmentSlot).where(
            AppointmentSlot.doctor_id == doctor_id,
            AppointmentSlot.is_active == True,
            AppointmentSlot.is_booked == False,
        )

        if date_from:
            stmt = stmt.where(AppointmentSlot.slot_datetime >= date_from)
        if date_to:
            stmt = stmt.where(AppointmentSlot.slot_datetime <= date_to)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_available_slots_for_clinic(
        self, clinic_id: int, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> List[AppointmentSlot]:
        """Get available slots for a clinic."""
        stmt = select(AppointmentSlot).where(
            AppointmentSlot.clinic_id == clinic_id,
            AppointmentSlot.is_active == True,
            AppointmentSlot.booked_count < AppointmentSlot.capacity,
        )

        if date_from:
            stmt = stmt.where(AppointmentSlot.slot_datetime >= date_from)
        if date_to:
            stmt = stmt.where(AppointmentSlot.slot_datetime <= date_to)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def delete_slot(self, slot_id: int) -> bool:
        """Soft delete a slot."""
        slot = await self.get_slot_by_id(slot_id)
        if not slot:
            return False

        slot.is_active = False
        self.db.add(slot)
        await self.db.commit()
        return True


# ============================================================================
# Appointment Repository
# ============================================================================


class AppointmentRepository:
    """Repository for appointment operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_appointment(self, **kwargs) -> Appointment:
        """Create a new appointment."""
        appointment = Appointment(**kwargs)
        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def get_appointment_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Get appointment by ID."""
        stmt = select(Appointment).where(Appointment.id == appointment_id, Appointment.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_appointment(self, appointment_id: int, **kwargs) -> Optional[Appointment]:
        """Update appointment."""
        appointment = await self.get_appointment_by_id(appointment_id)
        if not appointment:
            return None

        for key, value in kwargs.items():
            if hasattr(appointment, key) and value is not None:
                setattr(appointment, key, value)

        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def get_patient_appointments(
        self, patient_id: int, skip: int = 0, limit: int = 100
    ) -> List[Appointment]:
        """Get appointments for a patient."""
        stmt = (
            select(Appointment)
            .where(Appointment.patient_id == patient_id, Appointment.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_doctor_appointments(self, doctor_id: int, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Get appointments for a doctor."""
        stmt = (
            select(Appointment)
            .where(Appointment.doctor_id == doctor_id, Appointment.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def cancel_appointment(self, appointment_id: int, reason: str) -> Optional[Appointment]:
        """Cancel an appointment."""
        appointment = await self.get_appointment_by_id(appointment_id)
        if not appointment:
            return None

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.utcnow()
        appointment.cancelled_reason = reason

        self.db.add(appointment)
        await self.db.commit()
        await self.db.refresh(appointment)
        return appointment

    async def get_appointment_by_slot_id(self, slot_id: int) -> Optional[Appointment]:
        """Get appointment by slot ID."""
        stmt = select(Appointment).where(Appointment.slot_id == slot_id, Appointment.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_appointments(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """List all appointments."""
        stmt = (
            select(Appointment)
            .where(Appointment.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Appointment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
