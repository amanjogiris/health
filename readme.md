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
cd health
```

2. **Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirement.txt
```

4. **Configure environment**

Create a `.env` file in the project root:
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
│   Pydantic Schemas  │  Input validation & serialization
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
health/
├── app/
│   ├── __init__.py
│   ├── main.py               FastAPI application & all route handlers
│   ├── schemas.py            Pydantic request/response schemas
│   ├── crud.py               Repository layer (UserRepository, etc.)
│   ├── exceptions.py         Custom exception classes
│   ├── logging_config.py     Logging setup
│   ├── utils.py              Utility helpers
│   ├── db/
│   │   ├── base.py           SQLAlchemy DeclarativeBase
│   │   └── database.py       Async engine, session, get_db dependency
│   └── models/
│       ├── __init__.py       Re-exports all models
│       ├── mixins.py         TimestampMixin, SoftDeleteMixin
│       ├── user.py           User, UserRole
│       ├── patient.py        Patient
│       ├── clinic.py         Clinic
│       ├── doctor.py         Doctor
│       └── appointment.py    AppointmentSlot, Appointment, AppointmentStatus
├── alembic/
│   ├── env.py                Async migration environment
│   └── versions/             Migration scripts
├── alembic.ini               Alembic configuration
├── requirement.txt           Python dependencies
├── .env                      Environment variables (git-ignored)
└── readme.md
```

## Security

- **Password Hashing**: bcrypt via passlib with per-hash salt
- **JWT Authentication**: Stateless token-based auth (PyJWT)
- **Token Blacklist**: Logout invalidates tokens server-side (in-memory; swap to Redis for production)
- **CORS**: Configurable cross-origin access via FastAPI middleware
- **Input Validation**: Pydantic v2 schemas on all endpoints
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
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
curl -X POST "http://localhost:8000/api/v1/auth/logout?token=<jwt>"
# Returns { "message": "Successfully logged out" }
# The token is immediately invalidated — further requests with it return 401.
```

### Search Doctors by Specialty
```bash
curl "http://localhost:8000/api/v1/doctors?specialty=Cardiology"
```

### Create an Appointment Slot (Doctor/Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/slots?token=<jwt>" \
  -H "Content-Type: application/json" \
  -d '{"doctor_id":1,"clinic_id":1,"slot_datetime":"2026-04-01T10:00:00Z","duration_minutes":30,"capacity":1}'
```

### Book an Appointment
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/book?token=<jwt>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id":1,"doctor_id":1,"clinic_id":1,"slot_id":1,"reason_for_visit":"Regular checkup"}'
```

### Cancel an Appointment
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/1/cancel?token=<jwt>" \
  -H "Content-Type: application/json" \
  -d '{"cancelled_reason":"Scheduling conflict"}'
```

## Key Technologies

| Layer | Technology |
|---|---|
| Web framework | FastAPI |
| Database | PostgreSQL |
| Async driver | asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | PyJWT |
| Password hashing | passlib[bcrypt] |
| Validation | Pydantic v2 |
| Docs | Swagger / OpenAPI (built-in) |

## Testing

```bash
pytest --cov=app tests/
```

## Implementation Checklist

- [x] Split models into individual files (`user.py`, `patient.py`, `clinic.py`, `doctor.py`, `appointment.py`)
- [x] Repository pattern for data access
- [x] JWT authentication (register, login)
- [x] Logout with token blacklist
- [x] Role-based authorization
- [x] Patient management APIs
- [x] Doctor management APIs
- [x] Clinic management APIs
- [x] Appointment slot management
- [x] Appointment booking with concurrency handling
- [x] Async architecture (asyncpg + SQLAlchemy async)
- [x] Input validation with Pydantic
- [x] Error handling
- [x] Swagger / OpenAPI documentation
- [x] Database migrations (Alembic async)
- [x] Environment-based configuration (`.env`)
- [ ] Unit and integration tests
- [ ] Docker containerization
- [ ] CI/CD pipeline

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [JWT Best Practices (RFC 7519)](https://tools.ietf.org/html/rfc7519)

## License

This project is part of the ASCEND training program.

---

**Last Updated**: March 2, 2026  
**API Version**: 1.0.0


## 🎯 Overview

XYZ Health Services platform designed to address real-world healthcare challenges:

- ✅ Centralized appointment management
- ✅ Real-time doctor availability
- ✅ Multi-clinic support
- ✅ Role-based access (Patient, Doctor, Admin)
- ✅ Secure JWT authentication
- ✅ Async-ready architecture for scalability

## 📋 Features

### Authentication & Authorization
- User registration and login with JWT tokens
- Role-based access control (PATIENT, DOCTOR, ADMIN)
- Secure password hashing with bcrypt
- Token expiration and refresh mechanisms

### Patient Management
- Patient profile creation and updates
- Appointment history tracking
- Medical information storage (blood group, allergies, etc.)

### Doctor Management
- Doctor profile and specialty management
- Clinic assignments
- Availability management
- Patient load tracking

### Clinic Management
- Multi-clinic support
- Location-based clinic search
- Doctor-clinic mappings

### Appointment System
- Slot creation and availability management
- Concurrent booking handling
- Appointment cancellation
- Prevent double-bookings
- Slot capacity management

### Business Logic
- No double-booking enforcement
- Async appointment booking workflow
- Transaction handling for critical operations
- Automatic slot availability updates

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/amanjogiris/health.git
cd health
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirement.txt
```

4. **Setup PostgreSQL database**
```bash
# Create database
createdb health_db

# Update DATABASE_URL in app/database.py if needed
```

5. **Run migrations**
```bash
alembic upgrade head
```

6. **Start the server**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

### Authentication
```
POST   /api/v1/auth/register       - Register new user
POST   /api/v1/auth/login          - Login user
GET    /api/v1/auth/profile        - Get current user profile
```

### Patients
```
GET    /api/v1/patients/{id}       - Get patient details
PUT    /api/v1/patients/{id}       - Update patient details
GET    /api/v1/patients/{id}/appointments - Get patient's appointments
```

### Doctors
```
POST   /api/v1/doctors             - Create doctor (Admin)
GET    /api/v1/doctors             - List doctors
GET    /api/v1/doctors/{id}        - Get doctor details
PUT    /api/v1/doctors/{id}        - Update doctor details (Admin)
```

### Clinics
```
POST   /api/v1/clinics             - Create clinic (Admin)
GET    /api/v1/clinics             - List clinics
GET    /api/v1/clinics/{id}        - Get clinic details
GET    /api/v1/clinics/{id}/doctors - Get doctors at clinic
```

### Appointment Slots
```
POST   /api/v1/slots               - Create slot
GET    /api/v1/slots               - List available slots
DELETE /api/v1/slots/{id}          - Delete slot (Admin)
```

### Appointments
```
POST   /api/v1/appointments/book   - Book appointment
POST   /api/v1/appointments/{id}/cancel - Cancel appointment
GET    /api/v1/appointments/{id}   - Get appointment details
GET    /api/v1/appointments        - List all appointments (Admin)
```

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────┐
│   FastAPI Routes    │  (HTTP Layer)
├─────────────────────┤
│   Schemas (Pydantic)│  (Validation)
├─────────────────────┤
│   Repositories      │  (Data Access)
├─────────────────────┤
│   SQLAlchemy ORM    │  (ORM)
├─────────────────────┤
│   PostgreSQL        │  (Database)
└─────────────────────┘
```

### Project Structure

```
health_app/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & routes
│   ├── database.py          # Database configuration
│   ├── model.py             # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── crud.py              # Repository layer
├── alembic/                 # Database migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── requirement.txt          # Python dependencies
├── readme.md               # This file
└── alembic.ini            # Alembic configuration
```

## 🔐 Security Features

- **Password Hashing**: bcrypt with secure salting
- **JWT Authentication**: Token-based stateless auth
- **CORS Configuration**: Configurable cross-origin access
- **Input Validation**: Pydantic schemas validation
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **Role-Based Access**: Endpoint-level authorization
- **Soft Deletes**: Data recovery capability

## 🗄️ Database Models

### Users
- id, name, email, password_hash
- role (ADMIN, DOCTOR, PATIENT)
- is_verified, is_active, last_login
- created_at, updated_at

### Patients
- id, user_id, date_of_birth, blood_group
- allergies, emergency_contact
- created_at, updated_at, is_active

### Doctors
- id, user_id, clinic_id, specialty
- license_number, qualifications, experience_years
- max_patients_per_day
- created_at, updated_at, is_active

### Clinics
- id, name, address, phone, email
- city, state, zip_code
- created_at, updated_at, is_active

### AppointmentSlots
- id, doctor_id, clinic_id, slot_datetime
- duration_minutes, is_booked, capacity
- booked_count
- created_at, updated_at, is_active

### Appointments
- id, patient_id, doctor_id, clinic_id, slot_id
- status (PENDING, CONFIRMED, CANCELLED, COMPLETED, NO_SHOW)
- reason_for_visit, notes
- cancelled_at, cancelled_reason
- created_at, updated_at, is_active

## 🧪 Usage Examples

### Register a Patient
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepass123",
    "role": "patient",
    "mobile_no": "9876543210"
  }'
```

### Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### List Doctors by Specialty
```bash
curl -X GET "http://localhost:8000/api/v1/doctors?specialty=Cardiology" \
  -H "Authorization: Bearer <token>"
```

### Create Appointment Slot (Doctor/Admin)
```bash
curl -X POST "http://localhost:8000/api/v1/slots?token=<token>" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": 1,
    "clinic_id": 1,
    "slot_datetime": "2024-03-01T10:00:00Z",
    "duration_minutes": 30,
    "capacity": 1
  }'
```

### Book Appointment (Patient)
```bash
curl -X POST "http://localhost:8000/api/v1/appointments/book?token=<token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "clinic_id": 1,
    "slot_id": 1,
    "reason_for_visit": "Regular checkup"
  }'
```

## 🔄 Async Architecture

The system is built with async/await for:
- Slot availability checks
- Appointment booking workflows
- High-concurrency operations
- Database queries

This ensures non-blocking I/O and better performance under load.

## 📊 Design Patterns

### Repository Pattern
Abstraction for data access layer, making business logic independent of database implementation.

### Factory Pattern
Used for JWT token creation and authentication.

### Middleware Pattern
CORS and authentication middleware for cross-cutting concerns.

### Validation Pattern
Pydantic schemas for request/response validation.

## 🧩 Key Technologies

- **Framework**: FastAPI (async, type-safe, auto-documentation)
- **Database**: PostgreSQL with asyncpg for async support
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT with PyJWT
- **Password Hashing**: bcrypt via passlib
- **Validation**: Pydantic v2
- **API Documentation**: Swagger/OpenAPI
- **Migrations**: Alembic

## 🛠️ Configuration

### Environment Variables
Create a `.env` file:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/health_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database Configuration
Update `app/database.py`:
```python
DATABASE_URL = "postgresql+asyncpg://aman:123@localhost:5432/health_db"
```

## 📈 Performance Considerations

- **Async Operations**: Non-blocking I/O for improved throughput
- **Database Indexing**: Strategic indexes on frequently queried columns
- **Connection Pooling**: AsyncSessionLocal with optimal pool settings
- **Lazy Loading**: Prevent N+1 query problems
- **Caching Ready**: Structure supports Redis integration

## 🚦 Role-Based Access Control

| Endpoint | Patient | Doctor | Admin |
|----------|---------|--------|-------|
| Register | ✅ | ✅ | ✅ |
| Login | ✅ | ✅ | ✅ |
| Get Profile | ✅ | ✅ | ✅ |
| Manage Patients | ❌ | ❌ | ✅ |
| Manage Doctors | ❌ | ❌ | ✅ |
| Manage Clinics | ❌ | ❌ | ✅ |
| Create Slots | ❌ | ✅ | ✅ |
| Book Appointment | ✅ | ❌ | ❌ |
| View Appointments | ✅* | ✅* | ✅ |
| Cancel Appointment | ✅** | ✅** | ✅ |

*Own appointments only
**Own appointments only (Patient)

## 🔄 Workflow Examples

### Patient Appointment Booking Flow
1. Patient registers and creates profile
2. Patient searches for doctors by specialty/clinic
3. Patient views available slots
4. Patient books an appointment
5. Slot capacity is updated
6. Patient can view/cancel appointment

### Doctor Schedule Management Flow
1. Doctor registers with license info
2. Admin assigns doctor to clinic
3. Doctor creates appointment slots
4. Slot availability is managed
5. Doctor views booked appointments

## 📝 API Response Format

### Success Response
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "patient",
  ...
}
```

### Error Response
```json
{
  "detail": "Email already registered",
  "error_code": "VALIDATION_ERROR"
}
```

## 🧪 Testing

To run tests:
```bash
pytest --cov=app tests/
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [JWT Best Practices](https://tools.ietf.org/html/rfc7519)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write tests
4. Submit a pull request

## 📄 License

This project is part of ASCEND training program.

## 👨‍💼 Author

Aman Jogi (amanjogiris)

## ✅ Implementation Checklist

- [x] Database models for all entities
- [x] Repository pattern for data access
- [x] JWT authentication
- [x] Role-based authorization
- [x] Patient management APIs
- [x] Doctor management APIs
- [x] Clinic management APIs
- [x] Appointment slot management
- [x] Appointment booking with concurrency handling
- [x] Async architecture
- [x] Input validation with Pydantic
- [x] Error handling
- [x] API documentation (Swagger)
- [x] Database migrations
- [ ] Unit and integration tests
- [ ] Frontend UI (React/HTML+CSS+JS)
- [ ] GraphQL endpoint (optional)
- [ ] Docker containerization
- [ ] CI/CD pipeline

## 📞 Support

For issues and questions, please create an issue on GitHub.

---

**Last Updated**: February 24, 2024
**API Version**: 1.0.0
