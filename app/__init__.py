"""Health Services API Application Package."""

__version__ = "1.0.0"
__author__ = "Aman Jogi"
__description__ = "Comprehensive health appointment booking system API"

from app.model import Base, User, Patient, Doctor, Clinic, AppointmentSlot, Appointment

__all__ = [
    "Base",
    "User",
    "Patient",
    "Doctor",
    "Clinic",
    "AppointmentSlot",
    "Appointment",
]
