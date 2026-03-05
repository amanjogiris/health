"""Tests for slot management and appointment booking."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta


def _future(hours: int = 1) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


async def _setup_clinic_and_doctor(client):
    """Helper: create admin, doctor, clinic and return their ids + tokens."""
    admin_r = await client.post(
        "/api/v1/auth/register",
        json={"name": "Admin", "email": "slotadmin@hc.com", "password": "Admin1234", "role": "admin"},
    )
    admin_token = admin_r.json()["access_token"]

    doc_r = await client.post(
        "/api/v1/auth/register",
        json={"name": "Dr. Slot", "email": "drslot@hc.com", "password": "Doctor1234", "role": "doctor"},
    )
    doctor_user_id = doc_r.json()["user"]["id"]

    clinic_r = await client.post(
        "/api/v1/clinics",
        json={
            "name": "Slot Clinic",
            "address": "1 Slot St",
            "phone": "555-9999",
            "city": "NYC",
            "state": "NY",
            "zip_code": "10001",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    clinic_id = clinic_r.json()["id"]

    doctor_r = await client.post(
        "/api/v1/doctors",
        json={
            "user_id": doctor_user_id,
            "clinic_id": clinic_id,
            "specialty": "General",
            "license_number": "LIC-SLOT",
            "experience_years": 3,
            "max_patients_per_day": 20,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    doctor_id = doctor_r.json()["id"]

    return admin_token, clinic_id, doctor_id


@pytest.mark.asyncio
async def test_create_slot(client):
    admin_token, clinic_id, doctor_id = await _setup_clinic_and_doctor(client)

    resp = await client.post(
        "/api/v1/slots",
        json={
            "doctor_id": doctor_id,
            "clinic_id": clinic_id,
            "start_time": _future(1),
            "end_time": _future(2),
            "capacity": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["doctor_id"] == doctor_id
    assert not data["is_booked"]


@pytest.mark.asyncio
async def test_overlapping_slot_rejected(client):
    admin_token, clinic_id, doctor_id = await _setup_clinic_and_doctor(client)

    slot_payload = {
        "doctor_id": doctor_id,
        "clinic_id": clinic_id,
        "start_time": _future(1),
        "end_time": _future(2),
        "capacity": 1,
    }

    r1 = await client.post("/api/v1/slots", json=slot_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert r1.status_code == 201

    # Overlapping slot (starts in the middle of the first)
    slot_payload["start_time"] = _future(1)
    slot_payload["end_time"] = _future(3)
    r2 = await client.post("/api/v1/slots", json=slot_payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 422


@pytest.mark.asyncio
async def test_book_appointment(client):
    admin_token, clinic_id, doctor_id = await _setup_clinic_and_doctor(client)

    # Create a patient
    pat_r = await client.post(
        "/api/v1/auth/register",
        json={"name": "Pat", "email": "bookpat@hc.com", "password": "Patient1", "role": "patient"},
    )
    patient_token = pat_r.json()["access_token"]
    patient_user_id = pat_r.json()["user"]["id"]

    # Get the auto-created patient record
    pat_rec = await client.get(
        f"/api/v1/patients/{patient_user_id}",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    # patient id may differ from user id; try id=1
    patient_id = pat_rec.json().get("id", 1)

    # Create slot
    slot_r = await client.post(
        "/api/v1/slots",
        json={
            "doctor_id": doctor_id,
            "clinic_id": clinic_id,
            "start_time": _future(5),
            "end_time": _future(6),
            "capacity": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    slot_id = slot_r.json()["id"]

    # Book appointment
    book_r = await client.post(
        "/api/v1/appointments/book",
        json={
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "slot_id": slot_id,
            "clinic_id": clinic_id,
            "reason_for_visit": "Annual checkup",
        },
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert book_r.status_code == 201
    appt = book_r.json()
    assert appt["status"] == "pending"
    assert appt["slot_id"] == slot_id


@pytest.mark.asyncio
async def test_double_booking_rejected(client):
    admin_token, clinic_id, doctor_id = await _setup_clinic_and_doctor(client)

    p1 = await client.post(
        "/api/v1/auth/register",
        json={"name": "P1", "email": "p1@hc.com", "password": "Patient1", "role": "patient"},
    )
    p2 = await client.post(
        "/api/v1/auth/register",
        json={"name": "P2", "email": "p2@hc.com", "password": "Patient1", "role": "patient"},
    )
    t1 = p1.json()["access_token"]
    t2 = p2.json()["access_token"]

    slot_r = await client.post(
        "/api/v1/slots",
        json={
            "doctor_id": doctor_id,
            "clinic_id": clinic_id,
            "start_time": _future(10),
            "end_time": _future(11),
            "capacity": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    slot_id = slot_r.json()["id"]

    book1 = await client.post(
        "/api/v1/appointments/book",
        json={"patient_id": 3, "doctor_id": doctor_id, "slot_id": slot_id, "clinic_id": clinic_id},
        headers={"Authorization": f"Bearer {t1}"},
    )
    book2 = await client.post(
        "/api/v1/appointments/book",
        json={"patient_id": 4, "doctor_id": doctor_id, "slot_id": slot_id, "clinic_id": clinic_id},
        headers={"Authorization": f"Bearer {t2}"},
    )

    # One must succeed, one must fail
    statuses = {book1.status_code, book2.status_code}
    assert 201 in statuses
    assert statuses != {201, 201}
