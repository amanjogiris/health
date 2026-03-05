# v1 router aggregator
from fastapi import APIRouter

from app.api.v1 import (
    auth_routes,
    patient_routes,
    doctor_routes,
    clinic_routes,
    slot_routes,
    appointment_routes,
    admin_routes,
)

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_routes.router)
v1_router.include_router(patient_routes.router)
v1_router.include_router(doctor_routes.router)
v1_router.include_router(clinic_routes.router)
v1_router.include_router(slot_routes.router)
v1_router.include_router(appointment_routes.router)
v1_router.include_router(admin_routes.router)

__all__ = ["v1_router"]
