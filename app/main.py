"""Main FastAPI application."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import schemas
from app.crud import (
    UserRepository,
    PatientRepository,
    DoctorRepository,
    ClinicRepository,
    AppointmentSlotRepository,
    AppointmentRepository,
)
from app.model import User, UserRole, AppointmentStatus

# ============================================================================
# Configuration
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Health Services API",
    description="A comprehensive health appointment booking system API",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================================================
# Utility Functions
# ============================================================================


def create_access_token(user_id: int, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"sub": str(user_id), "role": role, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Query(None, description="JWT token"),
) -> User:
    """Get current authenticated user from token."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


def require_role(*allowed_roles: str):
    """Factory to create a role-checking dependency."""

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


# ============================================================================
# Authentication Endpoints
# ============================================================================


@app.post("/api/v1/auth/register", response_model=schemas.AuthToken, tags=["Authentication"])
async def register(user_data: schemas.UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    user_repo = UserRepository(db)

    # Check if user already exists
    existing_user = await user_repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = await user_repo.create_user(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role,
        mobile_no=user_data.mobile_no,
        address=user_data.address,
    )

    # If patient, create patient record
    if user.role == UserRole.PATIENT:
        patient_repo = PatientRepository(db)
        await patient_repo.create_patient(user_id=user.id)

    # Generate token
    token = create_access_token(user.id, user.role.value)

    return schemas.AuthToken(
        access_token=token,
        user=schemas.UserResponse(**user.to_dict()),
    )


@app.post("/api/v1/auth/login", response_model=schemas.AuthToken, tags=["Authentication"])
async def login(credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user."""
    user_repo = UserRepository(db)
    user = await user_repo.get_user_by_email(credentials.email)

    if not user or not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    await user_repo.update_user(user.id, last_login=datetime.utcnow())

    # Generate token
    token = create_access_token(user.id, user.role.value)

    return schemas.AuthToken(
        access_token=token,
        user=schemas.UserResponse(**user.to_dict()),
    )


@app.get("/api/v1/auth/profile", response_model=schemas.UserResponse, tags=["Authentication"])
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return schemas.UserResponse(**current_user.to_dict())


# ============================================================================
# Patient Endpoints
# ============================================================================


@app.get("/api/v1/patients/{patient_id}", response_model=schemas.PatientResponse, tags=["Patients"])
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Get patient details."""
    patient_repo = PatientRepository(db)
    patient = await patient_repo.get_patient_by_id(patient_id)

    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    return schemas.PatientResponse(**patient.__dict__)


@app.put("/api/v1/patients/{patient_id}", response_model=schemas.PatientResponse, tags=["Patients"])
async def update_patient(
    patient_id: int,
    patient_data: schemas.PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update patient details."""
    patient_repo = PatientRepository(db)
    patient = await patient_repo.get_patient_by_id(patient_id)

    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Check authorization
    if current_user.role != UserRole.ADMIN and patient.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this patient")

    updated_patient = await patient_repo.update_patient(patient_id, **patient_data.dict(exclude_unset=True))
    return schemas.PatientResponse(**updated_patient.__dict__)


@app.get("/api/v1/patients/{patient_id}/appointments", response_model=List[schemas.AppointmentResponse], tags=["Patients"])
async def get_patient_appointments(
    patient_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get patient's appointments."""
    appt_repo = AppointmentRepository(db)
    appointments = await appt_repo.get_patient_appointments(patient_id, skip, limit)

    return [schemas.AppointmentResponse(**appt.__dict__) for appt in appointments]


# ============================================================================
# Doctor Endpoints
# ============================================================================


@app.post("/api/v1/doctors", response_model=schemas.DoctorResponse, tags=["Doctors"])
async def create_doctor(
    doctor_data: schemas.DoctorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Create a new doctor (Admin only)."""
    doctor_repo = DoctorRepository(db)
    doctor = await doctor_repo.create_doctor(**doctor_data.dict())

    return schemas.DoctorResponse(**doctor.__dict__)


@app.get("/api/v1/doctors", response_model=List[schemas.DoctorResponse], tags=["Doctors"])
async def list_doctors(
    specialty: Optional[str] = Query(None),
    clinic_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List doctors with optional filters."""
    doctor_repo = DoctorRepository(db)

    if specialty or clinic_id:
        doctors = await doctor_repo.search_doctors(specialty=specialty, clinic_id=clinic_id)
    else:
        doctors = await doctor_repo.list_doctors(skip=skip, limit=limit)

    return [schemas.DoctorResponse(**doc.__dict__) for doc in doctors]


@app.get("/api/v1/doctors/{doctor_id}", response_model=schemas.DoctorResponse, tags=["Doctors"])
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)):
    """Get doctor details."""
    doctor_repo = DoctorRepository(db)
    doctor = await doctor_repo.get_doctor_by_id(doctor_id)

    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    return schemas.DoctorResponse(**doctor.__dict__)


@app.put("/api/v1/doctors/{doctor_id}", response_model=schemas.DoctorResponse, tags=["Doctors"])
async def update_doctor(
    doctor_id: int,
    doctor_data: schemas.DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Update doctor details (Admin only)."""
    doctor_repo = DoctorRepository(db)
    doctor = await doctor_repo.get_doctor_by_id(doctor_id)

    if not doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    updated_doctor = await doctor_repo.update_doctor(doctor_id, **doctor_data.dict(exclude_unset=True))
    return schemas.DoctorResponse(**updated_doctor.__dict__)


# ============================================================================
# Clinic Endpoints
# ============================================================================


@app.post("/api/v1/clinics", response_model=schemas.ClinicResponse, tags=["Clinics"])
async def create_clinic(
    clinic_data: schemas.ClinicCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Create a new clinic (Admin only)."""
    clinic_repo = ClinicRepository(db)
    clinic = await clinic_repo.create_clinic(**clinic_data.dict())

    return schemas.ClinicResponse(**clinic.__dict__)


@app.get("/api/v1/clinics", response_model=List[schemas.ClinicResponse], tags=["Clinics"])
async def list_clinics(
    city: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List clinics."""
    clinic_repo = ClinicRepository(db)

    if city:
        clinics = await clinic_repo.get_clinics_by_city(city)
    else:
        clinics = await clinic_repo.list_clinics(skip=skip, limit=limit)

    return [schemas.ClinicResponse(**clinic.__dict__) for clinic in clinics]


@app.get("/api/v1/clinics/{clinic_id}", response_model=schemas.ClinicResponse, tags=["Clinics"])
async def get_clinic(clinic_id: int, db: AsyncSession = Depends(get_db)):
    """Get clinic details."""
    clinic_repo = ClinicRepository(db)
    clinic = await clinic_repo.get_clinic_by_id(clinic_id)

    if not clinic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    return schemas.ClinicResponse(**clinic.__dict__)


@app.get("/api/v1/clinics/{clinic_id}/doctors", response_model=List[schemas.DoctorResponse], tags=["Clinics"])
async def get_clinic_doctors(clinic_id: int, db: AsyncSession = Depends(get_db)):
    """Get doctors at a clinic."""
    clinic_repo = ClinicRepository(db)
    clinic = await clinic_repo.get_clinic_by_id(clinic_id)

    if not clinic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")

    doctor_repo = DoctorRepository(db)
    doctors = await doctor_repo.get_doctors_by_clinic(clinic_id)

    return [schemas.DoctorResponse(**doc.__dict__) for doc in doctors]


# ============================================================================
# Appointment Slot Endpoints
# ============================================================================


@app.post("/api/v1/slots", response_model=schemas.AppointmentSlotResponse, tags=["Slots"])
async def create_slot(
    slot_data: schemas.AppointmentSlotCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "doctor")),
):
    """Create appointment slot."""
    slot_repo = AppointmentSlotRepository(db)
    slot = await slot_repo.create_slot(**slot_data.dict())

    return schemas.AppointmentSlotResponse(**slot.__dict__)


@app.get("/api/v1/slots", response_model=List[schemas.AppointmentSlotResponse], tags=["Slots"])
async def get_slots(
    doctor_id: Optional[int] = Query(None),
    clinic_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get available appointment slots."""
    slot_repo = AppointmentSlotRepository(db)

    if doctor_id:
        slots = await slot_repo.get_doctor_slots(doctor_id, date_from, date_to)
    elif clinic_id:
        slots = await slot_repo.get_available_slots_for_clinic(clinic_id, date_from, date_to)
    else:
        slots = await slot_repo.list_slots(skip=skip, limit=limit)

    return [schemas.AppointmentSlotResponse(**slot.__dict__) for slot in slots]


@app.delete("/api/v1/slots/{slot_id}", tags=["Slots"])
async def delete_slot(
    slot_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Delete appointment slot (Admin only)."""
    slot_repo = AppointmentSlotRepository(db)
    success = await slot_repo.delete_slot(slot_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

    return {"message": "Slot deleted successfully"}


# ============================================================================
# Appointment Endpoints
# ============================================================================


@app.post("/api/v1/appointments/book", response_model=schemas.AppointmentResponse, tags=["Appointments"])
async def book_appointment(
    appt_data: schemas.AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book an appointment."""
    appt_repo = AppointmentRepository(db)
    slot_repo = AppointmentSlotRepository(db)

    # Check if slot exists and is available
    slot = await slot_repo.get_slot_by_id(appt_data.slot_id)
    if not slot or slot.booked_count >= slot.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot not available")

    # Check if patient already has this appointment
    existing_appt = await appt_repo.get_appointment_by_slot_id(appt_data.slot_id)
    if existing_appt:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot already booked")

    # Create appointment
    appointment = await appt_repo.create_appointment(
        **appt_data.dict(),
        status=AppointmentStatus.PENDING,
    )

    # Update slot
    await slot_repo.update_slot(
        slot.id,
        booked_count=slot.booked_count + 1,
        is_booked=True if slot.booked_count + 1 >= slot.capacity else False,
    )

    return schemas.AppointmentResponse(**appointment.__dict__)


@app.post("/api/v1/appointments/{appointment_id}/cancel", response_model=schemas.AppointmentResponse, tags=["Appointments"])
async def cancel_appointment(
    appointment_id: int,
    cancel_data: schemas.AppointmentCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an appointment."""
    appt_repo = AppointmentRepository(db)
    appointment = await appt_repo.get_appointment_by_id(appointment_id)

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    # Check authorization
    if current_user.role == UserRole.PATIENT and appointment.patient_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this appointment")

    # Cancel appointment
    cancelled_appointment = await appt_repo.cancel_appointment(appointment_id, cancel_data.cancelled_reason)

    # Free up slot
    slot_repo = AppointmentSlotRepository(db)
    slot = await slot_repo.get_slot_by_id(appointment.slot_id)
    if slot:
        await slot_repo.update_slot(slot.id, booked_count=max(0, slot.booked_count - 1), is_booked=False)

    return schemas.AppointmentResponse(**cancelled_appointment.__dict__)


@app.get("/api/v1/appointments/{appointment_id}", response_model=schemas.AppointmentResponse, tags=["Appointments"])
async def get_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    """Get appointment details."""
    appt_repo = AppointmentRepository(db)
    appointment = await appt_repo.get_appointment_by_id(appointment_id)

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    return schemas.AppointmentResponse(**appointment.__dict__)


@app.get("/api/v1/appointments", response_model=List[schemas.AppointmentResponse], tags=["Appointments"])
async def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """List all appointments (Admin only)."""
    appt_repo = AppointmentRepository(db)
    appointments = await appt_repo.list_appointments(skip=skip, limit=limit)

    return [schemas.AppointmentResponse(**appt.__dict__) for appt in appointments]


# ============================================================================
# Health Check Endpoint
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)