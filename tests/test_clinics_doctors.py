"""Tests for clinic and doctor endpoints."""
from __future__ import annotations

import pytest


CLINIC_PAYLOAD = {
    "name": "City Health Clinic",
    "address": "123 Main St",
    "phone": "555-0100",
    "email": "info@cityhealth.com",
    "city": "Springfield",
    "state": "IL",
    "zip_code": "62701",
}

DOCTOR_PAYLOAD = {
    "user_id": None,  # filled in test
    "clinic_id": None,  # filled in test
    "specialty": "Cardiology",
    "license_number": "LIC-0001",
    "experience_years": 5,
    "max_patients_per_day": 10,
}


async def _admin_token(client) -> str:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "Admin", "email": "admin@hc.com", "password": "Admin1234", "role": "admin"},
    )
    return resp.json()["access_token"]


async def _doctor_user_token(client) -> tuple[str, int]:
    resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "Dr. Who", "email": "drwho@hc.com", "password": "Doctor1234", "role": "doctor"},
    )
    data = resp.json()
    return data["access_token"], data["user"]["id"]


@pytest.mark.asyncio
async def test_create_clinic_as_admin(client):
    token = await _admin_token(client)
    resp = await client.post(
        "/api/v1/clinics",
        json=CLINIC_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == CLINIC_PAYLOAD["name"]


@pytest.mark.asyncio
async def test_create_clinic_as_patient_forbidden(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"name": "Pat", "email": "pat@hc.com", "password": "Patient1", "role": "patient"},
    )
    token = resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/clinics",
        json=CLINIC_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_clinics(client):
    token = await _admin_token(client)
    await client.post(
        "/api/v1/clinics",
        json=CLINIC_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get("/api/v1/clinics")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_create_and_get_doctor(client):
    admin_token = await _admin_token(client)
    _, doctor_user_id = await _doctor_user_token(client)

    # Create clinic first
    clinic_resp = await client.post(
        "/api/v1/clinics",
        json=CLINIC_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    clinic_id = clinic_resp.json()["id"]

    doctor_payload = {**DOCTOR_PAYLOAD, "user_id": doctor_user_id, "clinic_id": clinic_id}
    create_resp = await client.post(
        "/api/v1/doctors",
        json=doctor_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    doctor_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/doctors/{doctor_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["specialty"] == "Cardiology"
