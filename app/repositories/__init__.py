# repositories package
from app.repositories.user_repository import UserRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.clinic_repository import ClinicRepository
from app.repositories.slot_repository import SlotRepository
from app.repositories.appointment_repository import AppointmentRepository

__all__ = [
    "UserRepository",
    "PatientRepository",
    "DoctorRepository",
    "ClinicRepository",
    "SlotRepository",
    "AppointmentRepository",
]
