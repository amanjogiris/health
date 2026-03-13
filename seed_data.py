#!/usr/bin/env python3
"""
Seed the database with realistic dummy data for local testing.

All user accounts share the password:  Test@1234

Usage (from health_backend/ with venv active):
    python seed_data.py
    python seed_data.py --clean   # drop existing seed data first
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.core.security import hash_password

COMMON_PASSWORD = "Test@1234"

# ── Seed data definitions ──────────────────────────────────────────────────────

CLINICS = [
    {
        "name": "Apollo Health Clinic",
        "address": "12 MG Road, Connaught Place",
        "phone": "011-40001234",
        "email": "apollo@healthportal.local",
        "city": "New Delhi",
        "state": "Delhi",
        "zip_code": "110001",
    },
    {
        "name": "Sunrise Medical Centre",
        "address": "45 Baner Road, Pune",
        "phone": "020-27001234",
        "email": "sunrise@healthportal.local",
        "city": "Pune",
        "state": "Maharashtra",
        "zip_code": "411045",
    },
    {
        "name": "City Care Hospital",
        "address": "78 Park Street, Kolkata",
        "phone": "033-22001234",
        "email": "citycare@healthportal.local",
        "city": "Kolkata",
        "state": "West Bengal",
        "zip_code": "700016",
    },
]

# Each doctor: user fields + doctor-specific fields (clinic index 0-based)
DOCTORS = [
    {
        "name": "Dr. Priya Sharma",
        "email": "priya.sharma@healthportal.local",
        "mobile_no": "9810001001",
        "clinic_idx": 0,
        "specialty": "Cardiology",
        "license_number": "DL-CARD-1001",
        "qualifications": "MBBS, MD (Cardiology), FACC",
        "experience_years": 12,
        "max_patients_per_day": 20,
        "consultation_duration_minutes": 30,
    },
    {
        "name": "Dr. Rohan Mehta",
        "email": "rohan.mehta@healthportal.local",
        "mobile_no": "9810001002",
        "clinic_idx": 0,
        "specialty": "Orthopedics",
        "license_number": "DL-ORTH-1002",
        "qualifications": "MBBS, MS (Ortho)",
        "experience_years": 8,
        "max_patients_per_day": 15,
        "consultation_duration_minutes": 20,
    },
    {
        "name": "Dr. Kavita Nair",
        "email": "kavita.nair@healthportal.local",
        "mobile_no": "9820001003",
        "clinic_idx": 1,
        "specialty": "Dermatology",
        "license_number": "MH-DERM-2003",
        "qualifications": "MBBS, DVD",
        "experience_years": 6,
        "max_patients_per_day": 25,
        "consultation_duration_minutes": 15,
    },
    {
        "name": "Dr. Anil Bose",
        "email": "anil.bose@healthportal.local",
        "mobile_no": "9830001004",
        "clinic_idx": 2,
        "specialty": "Neurology",
        "license_number": "WB-NEURO-3004",
        "qualifications": "MBBS, DM (Neurology)",
        "experience_years": 15,
        "max_patients_per_day": 12,
        "consultation_duration_minutes": 40,
    },
    {
        "name": "Dr. Sneha Iyer",
        "email": "sneha.iyer@healthportal.local",
        "mobile_no": "9820001005",
        "clinic_idx": 1,
        "specialty": "Pediatrics",
        "license_number": "MH-PEDI-2005",
        "qualifications": "MBBS, MD (Pediatrics)",
        "experience_years": 9,
        "max_patients_per_day": 30,
        "consultation_duration_minutes": 15,
    },
]

PATIENTS = [
    {
        "name": "Amit Kumar",
        "email": "amit.kumar@patient.local",
        "mobile_no": "9700001001",
        "date_of_birth": "1990-05-14",
        "blood_group": "O+",
        "allergies": "Penicillin",
        "emergency_contact": "9700001099",
    },
    {
        "name": "Sunita Devi",
        "email": "sunita.devi@patient.local",
        "mobile_no": "9700001002",
        "date_of_birth": "1985-11-22",
        "blood_group": "A+",
        "allergies": None,
        "emergency_contact": "9700001088",
    },
    {
        "name": "Ravi Patel",
        "email": "ravi.patel@patient.local",
        "mobile_no": "9700001003",
        "date_of_birth": "1978-03-09",
        "blood_group": "B-",
        "allergies": "Sulfa drugs",
        "emergency_contact": "9700001077",
    },
    {
        "name": "Meena Gupta",
        "email": "meena.gupta@patient.local",
        "mobile_no": "9700001004",
        "date_of_birth": "1995-07-30",
        "blood_group": "AB+",
        "allergies": None,
        "emergency_contact": "9700001066",
    },
    {
        "name": "Vikram Singh",
        "email": "vikram.singh@patient.local",
        "mobile_no": "9700001005",
        "date_of_birth": "2000-01-15",
        "blood_group": "O-",
        "allergies": "Aspirin",
        "emergency_contact": "9700001055",
    },
    {
        "name": "Pooja Reddy",
        "email": "pooja.reddy@patient.local",
        "mobile_no": "9700001006",
        "date_of_birth": "1993-09-18",
        "blood_group": "A-",
        "allergies": None,
        "emergency_contact": "9700001044",
    },
]

# Admin users
ADMINS = [
    {
        "name": "Admin User",
        "email": "admin@healthportal.local",
        "mobile_no": "9900001001",
        "role": "admin",
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def slot_times(start_date: date, days: int, start_h: int, end_h: int, duration_min: int):
    """Yield (start_dt, end_dt) tuples for each slot across `days` from start_date."""
    for d in range(days):
        current = datetime.combine(start_date + timedelta(days=d), time(start_h, 0), tzinfo=timezone.utc)
        end_of_day = datetime.combine(start_date + timedelta(days=d), time(end_h, 0), tzinfo=timezone.utc)
        while current + timedelta(minutes=duration_min) <= end_of_day:
            yield current, current + timedelta(minutes=duration_min)
            current += timedelta(minutes=duration_min)


# ── Main seeder ────────────────────────────────────────────────────────────────

async def seed(clean: bool) -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    pw_hash = hash_password(COMMON_PASSWORD)
    today = date.today()

    async with engine.begin() as conn:
        if clean:
            print("🧹  Cleaning seed data …")
            for tbl in ["appointments", "appointment_slots", "patients", "doctors",
                        "doctor_availability", "clinics"]:
                await conn.execute(text(f"DELETE FROM {tbl}"))
            # Remove seed users (keep super_admin)
            await conn.execute(
                text("DELETE FROM users WHERE email LIKE '%@healthportal.local' OR email LIKE '%@patient.local'")
            )
            print("    Done.\n")

        # ── 1. Clinics ─────────────────────────────────────────────────────────
        print("🏥  Creating clinics …")
        clinic_ids: list[int] = []
        for c in CLINICS:
            existing = (await conn.execute(
                text("SELECT id FROM clinics WHERE name = :name"), {"name": c["name"]}
            )).fetchone()
            if existing:
                clinic_ids.append(existing[0])
                print(f"    [skip] {c['name']} already exists (id={existing[0]})")
                continue
            row = (await conn.execute(
                text("""
                    INSERT INTO clinics (name, address, phone, email, city, state, zip_code, is_active)
                    VALUES (:name, :address, :phone, :email, :city, :state, :zip_code, true)
                    RETURNING id
                """),
                c,
            )).fetchone()
            clinic_ids.append(row[0])
            print(f"    [+] {c['name']}  (id={row[0]})")

        # ── 2. Admin user ──────────────────────────────────────────────────────
        print("\n🔑  Creating admin users …")
        for a in ADMINS:
            existing = (await conn.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": a["email"]}
            )).fetchone()
            if existing:
                print(f"    [skip] {a['email']} already exists")
                continue
            await conn.execute(
                text("""
                    INSERT INTO users (name, email, password_hash, role, mobile_no, is_verified, is_active)
                    VALUES (:name, :email, :pw, :role, :mobile, true, true)
                """),
                {"name": a["name"], "email": a["email"], "pw": pw_hash,
                 "role": a["role"], "mobile": a["mobile_no"]},
            )
            print(f"    [+] {a['email']}  role={a['role']}")

        # ── 3. Doctors ─────────────────────────────────────────────────────────
        print("\n👨‍⚕️  Creating doctors …")
        doctor_ids: list[int] = []
        doctor_clinic_ids: list[int] = []
        for d in DOCTORS:
            clinic_id = clinic_ids[d["clinic_idx"]]
            existing_user = (await conn.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": d["email"]}
            )).fetchone()
            if existing_user:
                user_id = existing_user[0]
                existing_doc = (await conn.execute(
                    text("SELECT id FROM doctors WHERE user_id = :uid"), {"uid": user_id}
                )).fetchone()
                if existing_doc:
                    doctor_ids.append(existing_doc[0])
                    doctor_clinic_ids.append(clinic_id)
                    print(f"    [skip] {d['name']} already exists")
                    continue
            else:
                row = (await conn.execute(
                    text("""
                        INSERT INTO users (name, email, password_hash, role, mobile_no, is_verified, is_active)
                        VALUES (:name, :email, :pw, 'doctor', :mobile, true, true)
                        RETURNING id
                    """),
                    {"name": d["name"], "email": d["email"], "pw": pw_hash, "mobile": d["mobile_no"]},
                )).fetchone()
                user_id = row[0]

            doc_row = (await conn.execute(
                text("""
                    INSERT INTO doctors
                        (user_id, clinic_id, specialty, license_number, qualifications,
                         experience_years, max_patients_per_day, consultation_duration_minutes, is_active)
                    VALUES
                        (:uid, :cid, :spec, :lic, :qual, :exp, :mpd, :dur, true)
                    RETURNING id
                """),
                {
                    "uid": user_id, "cid": clinic_id,
                    "spec": d["specialty"], "lic": d["license_number"],
                    "qual": d["qualifications"], "exp": d["experience_years"],
                    "mpd": d["max_patients_per_day"], "dur": d["consultation_duration_minutes"],
                },
            )).fetchone()
            doctor_ids.append(doc_row[0])
            doctor_clinic_ids.append(clinic_id)
            print(f"    [+] {d['name']}  ({d['specialty']}, clinic_id={clinic_id})")

        # ── 4. Patients ────────────────────────────────────────────────────────
        print("\n🧑‍🤝‍🧑  Creating patients …")
        patient_ids: list[int] = []
        for p in PATIENTS:
            existing_user = (await conn.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": p["email"]}
            )).fetchone()
            if existing_user:
                user_id = existing_user[0]
                existing_pat = (await conn.execute(
                    text("SELECT id FROM patients WHERE user_id = :uid"), {"uid": user_id}
                )).fetchone()
                if existing_pat:
                    patient_ids.append(existing_pat[0])
                    print(f"    [skip] {p['name']} already exists")
                    continue
            else:
                row = (await conn.execute(
                    text("""
                        INSERT INTO users (name, email, password_hash, role, mobile_no, is_verified, is_active)
                        VALUES (:name, :email, :pw, 'patient', :mobile, true, true)
                        RETURNING id
                    """),
                    {"name": p["name"], "email": p["email"], "pw": pw_hash, "mobile": p["mobile_no"]},
                )).fetchone()
                user_id = row[0]

            pat_row = (await conn.execute(
                text("""
                    INSERT INTO patients (user_id, date_of_birth, blood_group, allergies, emergency_contact, is_active)
                    VALUES (:uid, :dob, :bg, :allg, :ec, true)
                    RETURNING id
                """),
                {
                    "uid": user_id, "dob": p["date_of_birth"], "bg": p["blood_group"],
                    "allg": p["allergies"], "ec": p["emergency_contact"],
                },
            )).fetchone()
            patient_ids.append(pat_row[0])
            print(f"    [+] {p['name']}  ({p['email']})")

        # ── 5. Appointment slots (next 7 days, 09:00–17:00) ───────────────────
        print("\n📅  Creating appointment slots …")
        slot_ids_by_doctor: dict[int, list[int]] = {}
        for doc_id, clin_id, doc_def in zip(doctor_ids, doctor_clinic_ids, DOCTORS):
            dur = doc_def["consultation_duration_minutes"]
            slots_created = 0
            these_slots: list[int] = []
            for start_dt, end_dt in slot_times(today, 7, 9, 17, dur):
                row = (await conn.execute(
                    text("""
                        INSERT INTO appointment_slots
                            (doctor_id, clinic_id, start_time, end_time, is_booked, capacity, booked_count, is_active)
                        VALUES (:did, :cid, :st, :et, false, 1, 0, true)
                        ON CONFLICT DO NOTHING
                        RETURNING id
                    """),
                    {"did": doc_id, "cid": clin_id, "st": start_dt, "et": end_dt},
                )).fetchone()
                if row:
                    these_slots.append(row[0])
                    slots_created += 1
            slot_ids_by_doctor[doc_id] = these_slots
            print(f"    [+] Doctor id={doc_id}  → {slots_created} slots")

        # ── 6. Sample appointments ─────────────────────────────────────────────
        print("\n📋  Creating sample appointments …")
        # Map: (patient_idx, doctor_idx, slot_offset, status, reason, note)
        sample_appts = [
            (0, 0, 0, "BOOKED",     "Chest pain check",       None),
            (1, 0, 1, "BOOKED",     "Routine cardiac follow-up", None),
            (2, 1, 0, "BOOKED",     "Knee pain",              None),
            (3, 2, 0, "CANCELLED",  "Skin rash",              "Patient rescheduled"),
            (4, 3, 0, "BOOKED",     "Severe headache",        None),
            (5, 4, 0, "BOOKED",     "Child fever",            None),
            (0, 1, 2, "CANCELLED",  "Shoulder injury",        "No show"),
            (1, 2, 1, "BOOKED",     "Eczema follow-up",       None),
        ]

        appt_count = 0
        for pat_idx, doc_idx, slot_offset, status, reason, note in sample_appts:
            if pat_idx >= len(patient_ids) or doc_idx >= len(doctor_ids):
                continue
            pid = patient_ids[pat_idx]
            did = doctor_ids[doc_idx]
            cid = doctor_clinic_ids[doc_idx]
            slots = slot_ids_by_doctor.get(did, [])
            if slot_offset >= len(slots):
                continue
            sid = slots[slot_offset]

            # Check slot not already used
            taken = (await conn.execute(
                text("SELECT id FROM appointments WHERE slot_id = :sid"), {"sid": sid}
            )).fetchone()
            if taken:
                # pick next free slot
                for alt in slots[slot_offset + 1:]:
                    taken2 = (await conn.execute(
                        text("SELECT id FROM appointments WHERE slot_id = :sid"), {"sid": alt}
                    )).fetchone()
                    if not taken2:
                        sid = alt
                        break
                else:
                    continue

            cancelled_at = "NOW()" if status == "cancelled" else "NULL"
            await conn.execute(
                text(f"""
                    INSERT INTO appointments
                        (patient_id, doctor_id, clinic_id, slot_id, status,
                         reason_for_visit, notes,
                         cancelled_reason, cancelled_at, is_active)
                    VALUES
                        (:pid, :did, :cid, :sid, :status,
                         :reason, :note,
                         :cr, {"NOW()" if status == "CANCELLED" else "NULL"}, true)
                """),
                {
                    "pid": pid, "did": did, "cid": cid, "sid": sid,
                    "status": status, "reason": reason, "note": note,
                    "cr": note if status == "CANCELLED" else None,
                },
            )
            # Mark slot booked if status is booked
            if status == "BOOKED":
                await conn.execute(
                    text("UPDATE appointment_slots SET is_booked=true, booked_count=1 WHERE id=:sid"),
                    {"sid": sid},
                )
            appt_count += 1
            print(f"    [+] Patient #{pid} -> Doctor #{did}  [{status}]  '{reason}'")

    await engine.dispose()

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Seed complete!

🔑  Common password for ALL test accounts:
        Test@1234

👤  Admin
    admin@healthportal.local

👨‍⚕️  Doctors
    priya.sharma@healthportal.local   (Cardiology   – Apollo, Delhi)
    rohan.mehta@healthportal.local    (Orthopedics  – Apollo, Delhi)
    kavita.nair@healthportal.local    (Dermatology  – Sunrise, Pune)
    anil.bose@healthportal.local      (Neurology    – City Care, Kolkata)
    sneha.iyer@healthportal.local     (Pediatrics   – Sunrise, Pune)

🧑  Patients
    amit.kumar@patient.local
    sunita.devi@patient.local
    ravi.patel@patient.local
    meena.gupta@patient.local
    vikram.singh@patient.local
    pooja.reddy@patient.local

📋  {appt_count} sample appointments created
📅  Slots created for the next 7 days (09:00 – 17:00)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dummy data for local testing")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete existing seed data before inserting (keeps super_admin)",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.clean))


if __name__ == "__main__":
    main()
