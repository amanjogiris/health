"""Schemas package – re-exports all public schemas."""
from app.schemas.user_schema import UserRegister, UserLogin, UserResponse, TokenResponse, LogoutResponse
from app.schemas.patient_schema import PatientUpdate, PatientResponse
from app.schemas.doctor_schema import DoctorCreate, DoctorUpdate, DoctorResponse
from app.schemas.clinic_schema import ClinicCreate, ClinicUpdate, ClinicResponse
from app.schemas.slot_schema import SlotCreate, SlotUpdate, SlotResponse, SlotToggleResponse, SlotGenerateRange
from app.schemas.appointment_schema import AppointmentBook, AppointmentCancel, AppointmentResponse

__all__ = [
    "UserRegister", "UserLogin", "UserResponse", "TokenResponse", "LogoutResponse",
    "PatientUpdate", "PatientResponse",
    "DoctorCreate", "DoctorUpdate", "DoctorResponse",
    "ClinicCreate", "ClinicUpdate", "ClinicResponse",
    "SlotCreate", "SlotUpdate", "SlotResponse", "SlotToggleResponse", "SlotGenerateRange",
    "AppointmentBook", "AppointmentCancel", "AppointmentResponse",
]
