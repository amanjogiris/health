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
    leave_routes,
)
from app.api.v1.dynamic_slot_routes import appt_dynamic_router, doctor_dynamic_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_routes.router)
v1_router.include_router(patient_routes.router)
v1_router.include_router(doctor_routes.router)
v1_router.include_router(doctor_dynamic_router)   # GET /doctors/{id}/dynamic-slots
v1_router.include_router(clinic_routes.router)
v1_router.include_router(slot_routes.router)
v1_router.include_router(appt_dynamic_router)     # POST/GET /appointments/dynamic  ← must be before appointment_routes
v1_router.include_router(appointment_routes.router)  # GET /appointments/{id} catch-all is AFTER dynamic routes
v1_router.include_router(admin_routes.router)
v1_router.include_router(leave_routes.router)  # POST/GET/DELETE /doctors/{id}/leaves

__all__ = ["v1_router"]

