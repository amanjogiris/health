# Health Services API - Complete Implementation Guide

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [API Endpoints](#api-endpoints)
4. [Authentication Flow](#authentication-flow)
5. [Business Logic](#business-logic)
6. [Error Handling](#error-handling)
7. [Performance Optimization](#performance-optimization)

## System Architecture

### Layered Architecture Diagram
```
┌───────────────────────────────────────────────┐
│           Frontend (Web UI)                    │
│    (HTML/CSS/JS or React - Not Implemented)   │
└───────────────────────────────────────────────┘
                      ↑↓
┌───────────────────────────────────────────────┐
│         FastAPI Application Layer              │
│  - Route Handlers (@app.get, @app.post, etc)  │
│  - Request/Response Processing                 │
│  - CORS Middleware                             │
└───────────────────────────────────────────────┘
                      ↑↓
┌───────────────────────────────────────────────┐
│      Validation Layer (Pydantic Schemas)       │
│  - UserRegister, UserLogin                     │
│  - PatientCreate, DoctorCreate, etc           │
│  - AppointmentCreate, AppointmentCancel       │
└───────────────────────────────────────────────┘
                      ↑↓
┌───────────────────────────────────────────────┐
│      Repository/Service Layer (CRUD)           │
│  - UserRepository                              │
│  - PatientRepository                           │
│  - DoctorRepository                            │
│  - ClinicRepository                            │
│  - AppointmentSlotRepository                   │
│  - AppointmentRepository                       │
└───────────────────────────────────────────────┘
                      ↑↓
┌───────────────────────────────────────────────┐
│      ORM Layer (SQLAlchemy)                    │
│  - Session Management                          │
│  - Query Building                              │
│  - Relationship Mapping                        │
└───────────────────────────────────────────────┘
                      ↑↓
┌───────────────────────────────────────────────┐
│      Database (PostgreSQL)                     │
│  - users table                                 │
│  - patients table                              │
│  - doctors table                               │
│  - clinics table                               │
│  - appointment_slots table                     │
│  - appointments table                          │
└───────────────────────────────────────────────┘
```

## Database Schema

### ER Diagram

```
users (1) ──┬─── (1) patients
            ├─── (1) doctors
            └─── (?) appointments


doctors (1) ──┬─── (1) clinics
             ├─── (M) appointment_slots
             └─── (M) appointments


clinics (1) ──┬─── (M) doctors
             ├─── (M) appointment_slots
             └─── (M) appointments


appointment_slots (1) ──── (1) appointments


patients (1) ──── (M) appointments
```

### Table Details

#### users Table
```
id (PK) | name | email (UNIQUE) | password_hash | role | is_verified | is_active
created_at | updated_at | last_login | mobile_no | address
```

#### patients Table
```
id (PK) | user_id (FK, UNIQUE) | date_of_birth | blood_group | allergies
emergency_contact | is_active | created_at | updated_at
```

#### doctors Table
```
id (PK) | user_id (FK, UNIQUE) | clinic_id (FK) | specialty | license_number (UNIQUE)
qualifications | experience_years | max_patients_per_day | is_active | created_at | updated_at
```

#### clinics Table
```
id (PK) | name | address | phone | email | city | state | zip_code
is_active | created_at | updated_at
```

#### appointment_slots Table
```
id (PK) | doctor_id (FK) | clinic_id (FK) | slot_datetime | duration_minutes
is_booked | capacity | booked_count | is_active | created_at | updated_at
```

#### appointments Table
```
id (PK) | patient_id (FK) | doctor_id (FK) | clinic_id (FK) | slot_id (FK, UNIQUE)
status (ENUM) | reason_for_visit | notes | cancelled_at | cancelled_reason
is_active | created_at | updated_at
```

## API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/register
Register a new user
```
Request:
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "role": "patient|doctor|admin",
  "mobile_no": "9876543210",
  "address": "123 Main St"
}

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "role": "patient",
    ...
  }
}
```

#### POST /api/v1/auth/login
Login user
```
Request:
{
  "email": "john@example.com",
  "password": "SecurePass123"
}

Response: 200 OK
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

#### GET /api/v1/auth/profile
Get current user profile
```
Query Parameters:
- token: JWT token

Response: 200 OK
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "patient",
  ...
}
```

### Patient Endpoints

#### GET /api/v1/patients/{patient_id}
Get patient details
```
Response: 200 OK
{
  "id": 1,
  "user_id": 1,
  "date_of_birth": "1990-01-15",
  "blood_group": "O+",
  ...
}
```

#### PUT /api/v1/patients/{patient_id}
Update patient details
```
Request:
{
  "date_of_birth": "1990-01-15",
  "blood_group": "O+",
  "allergies": "Penicillin",
  "emergency_contact": "9876543210"
}

Response: 200 OK
{...updated patient...}
```

#### GET /api/v1/patients/{patient_id}/appointments
Get patient's appointments
```
Query Parameters:
- skip: 0 (pagination offset)
- limit: 100 (pagination limit)

Response: 200 OK
[{appointment1}, {appointment2}, ...]
```

### Doctor Endpoints

#### POST /api/v1/doctors
Create doctor (Admin only)
```
Request:
{
  "user_id": 1,
  "clinic_id": 1,
  "specialty": "Cardiology",
  "license_number": "LIC123456",
  "qualifications": "MD, Board Certified",
  "experience_years": 5,
  "max_patients_per_day": 10
}

Response: 201 Created
{...doctor...}
```

#### GET /api/v1/doctors
List doctors
```
Query Parameters:
- specialty: "Cardiology" (optional)
- clinic_id: 1 (optional)
- skip: 0
- limit: 100

Response: 200 OK
[{doctor1}, {doctor2}, ...]
```

#### GET /api/v1/doctors/{doctor_id}
Get doctor details
```
Response: 200 OK
{...doctor...}
```

#### PUT /api/v1/doctors/{doctor_id}
Update doctor (Admin only)
```
Request:
{
  "specialty": "Cardiology",
  "experience_years": 6,
  "max_patients_per_day": 15
}

Response: 200 OK
{...updated doctor...}
```

### Clinic Endpoints

#### POST /api/v1/clinics
Create clinic (Admin only)
```
Request:
{
  "name": "City Health Center",
  "address": "123 Main St",
  "phone": "9876543210",
  "email": "info@cityhealthcenter.com",
  "city": "New York",
  "state": "NY",
  "zip_code": "10001"
}

Response: 201 Created
{...clinic...}
```

#### GET /api/v1/clinics
List clinics
```
Query Parameters:
- city: "New York" (optional)
- skip: 0
- limit: 100

Response: 200 OK
[{clinic1}, {clinic2}, ...]
```

#### GET /api/v1/clinics/{clinic_id}
Get clinic details
```
Response: 200 OK
{...clinic...}
```

#### GET /api/v1/clinics/{clinic_id}/doctors
Get doctors at clinic
```
Response: 200 OK
[{doctor1}, {doctor2}, ...]
```

### Appointment Slot Endpoints

#### POST /api/v1/slots
Create appointment slot (Doctor/Admin)
```
Request:
{
  "doctor_id": 1,
  "clinic_id": 1,
  "slot_datetime": "2024-03-01T10:00:00Z",
  "duration_minutes": 30,
  "capacity": 1
}

Response: 201 Created
{
  "id": 1,
  "doctor_id": 1,
  "clinic_id": 1,
  "slot_datetime": "2024-03-01T10:00:00Z",
  "is_booked": false,
  "booked_count": 0,
  "available_slots": 1,
  ...
}
```

#### GET /api/v1/slots
Get available slots
```
Query Parameters:
- doctor_id: 1 (optional)
- clinic_id: 1 (optional)
- date_from: "2024-03-01T00:00:00Z" (optional)
- date_to: "2024-03-31T23:59:59Z" (optional)
- skip: 0
- limit: 100

Response: 200 OK
[{slot1}, {slot2}, ...]
```

#### DELETE /api/v1/slots/{slot_id}
Delete slot (Admin only)
```
Response: 200 OK
{"message": "Slot deleted successfully"}
```

### Appointment Endpoints

#### POST /api/v1/appointments/book
Book appointment
```
Request:
{
  "patient_id": 1,
  "doctor_id": 1,
  "clinic_id": 1,
  "slot_id": 1,
  "reason_for_visit": "Regular checkup"
}

Response: 201 Created
{
  "id": 1,
  "patient_id": 1,
  "doctor_id": 1,
  "clinic_id": 1,
  "slot_id": 1,
  "status": "pending",
  "reason_for_visit": "Regular checkup",
  ...
}
```

#### POST /api/v1/appointments/{appointment_id}/cancel
Cancel appointment
```
Request:
{
  "cancelled_reason": "Unable to attend due to emergency"
}

Response: 200 OK
{
  "id": 1,
  "status": "cancelled",
  "cancelled_at": "2024-02-24T15:30:00Z",
  ...
}
```

#### GET /api/v1/appointments/{appointment_id}
Get appointment details
```
Response: 200 OK
{...appointment...}
```

#### GET /api/v1/appointments
List all appointments (Admin only)
```
Query Parameters:
- skip: 0
- limit: 100

Response: 200 OK
[{appointment1}, {appointment2}, ...]
```

## Authentication Flow

### JWT Token Flow
```
1. User Registration
   User Data → Register Endpoint → Hash Password → Create User → Generate JWT Token → Return Token

2. User Login
   Email + Password → Login Endpoint → Verify Password → Generate JWT Token → Return Token

3. Authenticated Request
   Token → API Endpoint → Verify Token → Extract User ID → Get User from DB → Process Request

4. Token Validation
   JWT Token → Decode → Validate Signature → Check Expiration → Extract Claims
```

### Token Structure
```
Header: {"alg": "HS256", "typ": "JWT"}
Payload: {"sub": "1", "role": "patient", "exp": 1708878000}
Signature: HMACSHA256(header.payload, secret)

Example Token:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxIiwicm9sZSI6InBhdGllbnQiLCJleHAiOjE3MDg4NzgwMDB9.
signature_here
```

## Business Logic

### Appointment Booking Logic
```
1. User requests to book appointment with slot_id

2. Verify:
   - Slot exists
   - Slot has available capacity (booked_count < capacity)
   - Slot not already booked by this patient
   - Slot datetime is in future

3. Create Appointment:
   - Insert appointment record with status = PENDING
   - Update slot.booked_count += 1
   - If booked_count >= capacity, set slot.is_booked = true

4. Return:
   - Appointment details with confirmation
```

### Appointment Cancellation Logic
```
1. User requests to cancel appointment

2. Verify:
   - Appointment exists
   - Appointment status is not already CANCELLED
   - User is authorized (patient can cancel own, admin can cancel any)

3. Cancel Appointment:
   - Set status = CANCELLED
   - Set cancelled_at = current_time
   - Set cancelled_reason = provided reason

4. Free Up Slot:
   - Get associated slot
   - Decrease slot.booked_count by 1
   - If booked_count < capacity, set slot.is_booked = false

5. Return:
   - Updated appointment details
```

### Slot Availability Logic
```
1. Doctor creates appointment slots

2. System validates:
   - slot_datetime is in future
   - No overlapping slots for same doctor at same time

3. Capacity Management:
   - Each slot has capacity (default 1)
   - Can have booked_count from 0 to capacity
   - is_booked = true only when booked_count >= capacity

4. Listing available slots:
   - Filter: is_active = true AND booked_count < capacity
   - Include capacity and booked_count in response
   - Calculate available_slots = capacity - booked_count
```

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-02-24T15:30:00Z"
}
```

### Common HTTP Status Codes
- 200 OK - Successful GET/PUT request
- 201 Created - Successful POST request
- 400 Bad Request - Validation error or business logic error
- 401 Unauthorized - Missing or invalid authentication token
- 403 Forbidden - Authenticated but insufficient permissions
- 404 Not Found - Resource not found
- 409 Conflict - Duplicate entry or conflicting operation
- 500 Internal Server Error - Server error

### Custom Exception Classes
- ValidationException (400)
- AuthenticationException (401)
- AuthorizationException (403)
- ResourceNotFoundException (404)
- ConflictException (409)
- SlotUnavailableException (409)
- DuplicateBookingException (409)
- EmailAlreadyRegisteredException (409)

## Performance Optimization

### Database Indexing
```
- users.email (for login lookups)
- patients.user_id (for patient-user joins)
- doctors.clinic_id (for clinic doctor listings)
- doctors.user_id (for doctor user lookups)
- appointment_slots.doctor_id (for doctor slot queries)
- appointment_slots.clinic_id (for clinic slot queries)
- appointment_slots.slot_datetime (for date range queries)
- appointments.patient_id (for patient appointment history)
- appointments.doctor_id (for doctor appointment listings)
- appointments.slot_id (for slot-appointment relationships)
```

### Query Optimization
- Use SELECT with specific columns, not SELECT *
- Apply pagination with skip/limit
- Use efficient joins in ORM
- Filter at database level, not in Python

### Async Operations
- All database queries are async (AsyncSession)
- Non-blocking I/O for concurrent operations
- Improved throughput under load

### Caching Opportunities
- Cache frequently accessed doctors by specialty
- Cache clinic information
- Cache available slots for next 7 days
- Cache user profile after login

## Future Enhancements

1. **Frontend Implementation**
   - React-based web UI
   - Patient dashboard
   - Doctor management interface
   - Admin control panel

2. **GraphQL API**
   - Optimized data fetching
   - Single query for doctor + slots + clinic info

3. **Notifications**
   - Email reminders for appointments
   - SMS notifications
   - Push notifications for mobile app

4. **Advanced Features**
   - Prescription management
   - Medical history
   - Telemedicine integration
   - Payment processing

5. **DevOps**
   - Docker containerization
   - CI/CD pipeline
   - Load testing
   - API monitoring and logging

6. **Security**
   - Two-factor authentication
   - Refresh tokens
   - Rate limiting
   - API key management

---

**Document Version**: 1.0.0
**Last Updated**: February 24, 2024
