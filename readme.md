# Health Services API

A comprehensive, scalable health appointment booking system built with FastAPI, SQLAlchemy, and PostgreSQL. This API provides complete functionality for managing doctors, patients, clinics, and appointments with JWT-based authentication and role-based access control.

## Overview

XYZ Health Services platform designed to address real-world healthcare challenges:

- Centralized appointment management
- Real-time doctor availability
- Multi-clinic support
- Role-based access (Patient, Doctor, Admin)
- Secure JWT authentication with token blacklist logout
- Async-ready architecture for scalability

## Features

### Authentication & Authorization
- User registration and login with JWT tokens
- Logout with server-side token invalidation (blacklist)
- Role-based access control (PATIENT, DOCTOR, ADMIN)
- Secure password hashing with bcrypt
- Token expiration (configurable, default 30 min)

### Patient Management
- Patient profile creation and updates
- Appointment history tracking
- Medical information storage (blood group, allergies, emergency contact)

### Doctor Management
- Doctor profile and specialty management
- Clinic assignments
- Availability slot management
- Patient load tracking (`max_patients_per_day`)

### Clinic Management
- Multi-clinic support
- City-based clinic search
- Doctor-clinic mappings

### Appointment System
- Slot creation with capacity management
- Concurrent booking handling
- Appointment cancellation with reason tracking
- Double-booking prevention
- Automatic slot availability updates

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/amanjogiris/health.git
cd health/health_backend
```

2. **Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**

Create a `.env` file in `health_backend/`:
```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=health_db

SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> Passwords with special characters (`@`, `#`, `%`) are safe — the app uses `urllib.parse.quote_plus` to encode them automatically.

5. **Create PostgreSQL database**
```bash
createdb health_db
```

6. **Run migrations**
```bash
alembic upgrade head
```

7. **Start the server**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
```
POST   /api/v1/auth/register       Register a new user (returns JWT)
POST   /api/v1/auth/login          Login and receive JWT
POST   /api/v1/auth/logout         Logout and invalidate JWT  [auth required]
GET    /api/v1/auth/profile        Get current user profile   [auth required]
```

### Patients
```
GET    /api/v1/patients/{id}                    Get patient details
PUT    /api/v1/patients/{id}                    Update patient details  [auth]
GET    /api/v1/patients/{id}/appointments       Get patient's appointments
```

### Doctors
```
POST   /api/v1/doctors             Create doctor               [admin]
GET    /api/v1/doctors             List / search doctors
GET    /api/v1/doctors/{id}        Get doctor details
PUT    /api/v1/doctors/{id}        Update doctor details       [admin]
```

### Clinics
```
POST   /api/v1/clinics             Create clinic               [admin]
GET    /api/v1/clinics             List clinics (filter by city)
GET    /api/v1/clinics/{id}        Get clinic details
GET    /api/v1/clinics/{id}/doctors  Get doctors at a clinic
```

### Appointment Slots
```
POST   /api/v1/slots               Create slot                 [admin, doctor]
GET    /api/v1/slots               List available slots
DELETE /api/v1/slots/{id}          Delete slot                 [admin]
```

### Appointments
```
POST   /api/v1/appointments/book           Book appointment    [auth]
POST   /api/v1/appointments/{id}/cancel    Cancel appointment  [auth]
GET    /api/v1/appointments/{id}           Get appointment details
GET    /api/v1/appointments                List all appointments [admin]
```

## Architecture

### Layered Architecture

```
┌─────────────────────┐
│   FastAPI Routes    │  HTTP layer — request/response handling
├─────────────────────┤
│   Pydantic Schemas  │  Input validation & serialisation
├─────────────────────┤
│   Service Layer     │  Business logic & orchestration
├─────────────────────┤
│   Repositories      │  Data access (CRUD) layer
├─────────────────────┤
│   SQLAlchemy ORM    │  Async ORM with 2.0-style queries
├─────────────────────┤
│   PostgreSQL        │  Persistent storage
└─────────────────────┘
```

### Project Structure

```
health_backend/
├── app/
│   ├── __init__.py
│   ├── main.py               FastAPI application & router registration
│   ├── config.py             Settings loaded from .env via pydantic-settings
│   ├── crud.py               Legacy CRUD helpers (superseded by repositories)
│   ├── exceptions.py         Custom exception classes
│   ├── logging_config.py     Logging setup
│   ├── schemas.py            Top-level Pydantic schemas
│   ├── utils.py              Utility helpers
│   ├── api/
│   │   └── v1/               Versioned route handlers
│   ├── core/
│   │   ├── dependencies.py   FastAPI dependency injection helpers
│   │   ├── logging.py        Request-level logging middleware
│   │   └── security.py       JWT creation & verification
│   ├── db/
│   │   ├── base.py           SQLAlchemy DeclarativeBase
│   │   ├── database.py       Async engine & session factory
│   │   └── session.py        get_db dependency
│   ├── models/
│   │   ├── mixins.py         TimestampMixin, SoftDeleteMixin
│   │   ├── user.py           User, UserRole
│   │   ├── patient.py        Patient
│   │   ├── clinic.py         Clinic
│   │   ├── doctor.py         Doctor
│   │   └── appointment.py    AppointmentSlot, Appointment, AppointmentStatus
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── patient_repository.py
│   │   ├── doctor_repository.py
│   │   ├── clinic_repository.py
│   │   ├── appointment_repository.py
│   │   ├── availability_repository.py
│   │   └── slot_repository.py
│   ├── schemas/              Per-domain Pydantic schemas
│   │   ├── appointment_schema.py
│   │   ├── clinic_schema.py
│   │   └── doctor_schema.py
│   └── services/             Business logic layer
├── alembic/
│   ├── env.py                Async migration environment
│   └── versions/             Migration scripts
├── tests/
│   ├── conftest.py           Shared fixtures (in-memory SQLite)
│   ├── test_auth.py
│   ├── test_clinics_doctors.py
│   ├── test_security.py
│   ├── test_services.py
│   └── test_slots_appointments.py
├── alembic.ini               Alembic configuration
├── docker-compose.yml        Full-stack Docker Compose (db + backend + frontend)
├── Dockerfile                Backend container image
├── requirements.txt          Python dependencies
├── seed_data.py              Database seed script
├── create_superadmin.py      Superadmin creation helper
└── readme.md
```

## Security

- **Password Hashing**: bcrypt via passlib with per-hash salt
- **JWT Authentication**: Stateless token-based auth (PyJWT)
- **Token Blacklist**: Logout invalidates tokens server-side (in-memory; swap to Redis for production)
- **CORS**: Configurable cross-origin access via FastAPI middleware
- **Input Validation**: Pydantic v2 schemas on all endpoints
- **SQL Injection Prevention**: SQLAlchemy parameterised queries
- **Role-Based Access Control**: Per-endpoint role enforcement
- **Soft Deletes**: `is_active` flag preserves data recoverability
- **URL-safe Credentials**: `quote_plus` encoding for special chars in DB passwords

## Database Models

| Model | Key Fields |
|---|---|
| **User** | id, name, email, password_hash, role, is_verified, is_active, last_login |
| **Patient** | id, user_id, date_of_birth, blood_group, allergies, emergency_contact |
| **Doctor** | id, user_id, clinic_id, specialty, license_number, experience_years, max_patients_per_day |
| **Clinic** | id, name, address, phone, email, city, state, zip_code |
| **AppointmentSlot** | id, doctor_id, clinic_id, slot_datetime, duration_minutes, capacity, booked_count, is_booked |
| **Appointment** | id, patient_id, doctor_id, clinic_id, slot_id, status, reason_for_visit, notes, cancelled_at |

All models inherit `TimestampMixin` (`created_at`, `updated_at`) and `SoftDeleteMixin` (`is_active`).

## Role-Based Access Control

| Endpoint | Patient | Doctor | Admin |
|---|---|---|---|
| Register / Login / Logout | ✅ | ✅ | ✅ |
| Get Profile | ✅ | ✅ | ✅ |
| Update own Patient record | ✅ | ❌ | ✅ |
| Create / Update Doctor | ❌ | ❌ | ✅ |
| Create / Update Clinic | ❌ | ❌ | ✅ |
| Create Slots | ❌ | ✅ | ✅ |
| Delete Slots | ❌ | ❌ | ✅ |
| Book Appointment | ✅ | ❌ | ❌ |
| Cancel own Appointment | ✅ | ✅ | ✅ |
| List all Appointments | ❌ | ❌ | ✅ |

## Usage Examples

### Register
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@example.com","password":"Secret@123","role":"patient"}'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"Secret@123"}'
# Returns { "access_token": "<jwt>", ... }
```

### Logout
```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer <jwt>"
# Returns { "message": "Successfully logged out" }
# The token is immediately invalidated — further requests with it return 401.
```

### Search Doctors by Specialty
```bash
curl "http://localhost:8000/api/v1/doctors?specialty=Cardiology" \
  -H "Authorization: Bearer <jwt>"
```

### Create an Appointment Slot (Doctor/Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/slots" \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"doctor_id":1,"clinic_id":1,"slot_datetime":"2026-04-01T10:00:00Z","duration_minutes":30,"capacity":1}'
```

### Book an Appointment
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/book" \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":1,"doctor_id":1,"clinic_id":1,"slot_id":1,"reason_for_visit":"Regular checkup"}'
```

### Cancel an Appointment
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/1/cancel" \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"cancelled_reason":"Scheduling conflict"}'
```

## Key Technologies

| Layer | Technology |
|---|---|
| Web framework | FastAPI 0.129 |
| Database | PostgreSQL 16 |
| Async driver | asyncpg 0.31 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic 1.18 |
| Auth | PyJWT 2.9 |
| Password hashing | passlib[bcrypt] 1.7 |
| Validation | Pydantic v2 |
| Settings | pydantic-settings 2.0 |
| Server | uvicorn 0.41 |
| Docs | Swagger / OpenAPI (built-in) |
| Containerisation | Docker + Docker Compose |

## Testing

Tests use an in-memory SQLite database and run via pytest with httpx's async test client.

```bash
pytest --cov=app tests/
```

| File | Scope |
|---|---|
| `test_auth.py` | Registration, login, logout, profile |
| `test_clinics_doctors.py` | Clinic and doctor CRUD |
| `test_security.py` | JWT creation, verification, blacklist |
| `test_services.py` | Service-layer business logic |
| `test_slots_appointments.py` | Slot creation, booking, cancellation |

## Implementation Checklist

- [x] Split models into individual files (`user.py`, `patient.py`, `clinic.py`, `doctor.py`, `appointment.py`)
- [x] Repository pattern for data access
- [x] Service layer for business logic
- [x] JWT authentication (register, login)
- [x] Logout with token blacklist
- [x] Role-based authorization
- [x] Patient management APIs
- [x] Doctor management APIs
- [x] Clinic management APIs
- [x] Appointment slot management
- [x] Appointment booking with concurrency handling
- [x] Async architecture (asyncpg + SQLAlchemy async)
- [x] Input validation with Pydantic v2
- [x] Custom exception handling
- [x] Structured logging
- [x] Swagger / OpenAPI documentation
- [x] Database migrations (Alembic async)
- [x] Environment-based configuration (`.env` + pydantic-settings)
- [x] Unit and integration tests
- [x] Docker containerisation (Dockerfile + docker-compose.yml)
- [x] Seed data & superadmin creation scripts
- [ ] CI/CD pipeline
- [ ] Redis token blacklist (production hardening)

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [JWT Best Practices (RFC 7519)](https://tools.ietf.org/html/rfc7519)

## License

This project is part of the ASCEND training program.

---

**Last Updated**: March 13, 2026  
**API Version**: 1.0.0