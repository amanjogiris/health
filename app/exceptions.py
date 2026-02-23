"""Custom exceptions and error handling."""

from fastapi import HTTPException, status
from datetime import datetime


class BaseApplicationException(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "message": self.message,
                "error_code": self.error_code,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


class ValidationException(BaseApplicationException):
    """Raised when validation fails."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationException(BaseApplicationException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", status.HTTP_401_UNAUTHORIZED)


class AuthorizationException(BaseApplicationException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR", status.HTTP_403_FORBIDDEN)


class ResourceNotFoundException(BaseApplicationException):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, resource_id=None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, "RESOURCE_NOT_FOUND", status.HTTP_404_NOT_FOUND)


class ConflictException(BaseApplicationException):
    """Raised when there's a conflict (e.g., duplicate entry)."""

    def __init__(self, message: str, error_code: str = "CONFLICT"):
        super().__init__(message, error_code, status.HTTP_409_CONFLICT)


class SlotNotFoundException(ResourceNotFoundException):
    """Raised when a slot is not found."""

    def __init__(self, slot_id: int = None):
        super().__init__("Slot", slot_id)


class DoctorNotFoundException(ResourceNotFoundException):
    """Raised when a doctor is not found."""

    def __init__(self, doctor_id: int = None):
        super().__init__("Doctor", doctor_id)


class PatientNotFoundException(ResourceNotFoundException):
    """Raised when a patient is not found."""

    def __init__(self, patient_id: int = None):
        super().__init__("Patient", patient_id)


class ClinicNotFoundException(ResourceNotFoundException):
    """Raised when a clinic is not found."""

    def __init__(self, clinic_id: int = None):
        super().__init__("Clinic", clinic_id)


class UserNotFoundException(ResourceNotFoundException):
    """Raised when a user is not found."""

    def __init__(self, user_id: int = None):
        super().__init__("User", user_id)


class SlotUnavailableException(ConflictException):
    """Raised when a slot is not available for booking."""

    def __init__(self):
        super().__init__("Slot is not available for booking", "SLOT_UNAVAILABLE")


class AppointmentException(BaseApplicationException):
    """Raised when appointment operation fails."""

    def __init__(self, message: str, error_code: str = "APPOINTMENT_ERROR"):
        super().__init__(message, error_code, status.HTTP_400_BAD_REQUEST)


class DuplicateBookingException(ConflictException):
    """Raised when trying to book an already booked slot."""

    def __init__(self):
        super().__init__("Slot is already booked", "DUPLICATE_BOOKING")


class EmailAlreadyRegisteredException(ConflictException):
    """Raised when email is already registered."""

    def __init__(self, email: str):
        super().__init__(f"Email {email} is already registered", "EMAIL_ALREADY_EXISTS")


class InvalidCredentialsException(AuthenticationException):
    """Raised when credentials are invalid."""

    def __init__(self):
        super().__init__("Invalid email or password")


class InvalidTokenException(AuthenticationException):
    """Raised when token is invalid."""

    def __init__(self):
        super().__init__("Invalid or expired token")


class UserInactiveException(AuthorizationException):
    """Raised when user account is inactive."""

    def __init__(self):
        super().__init__("User account is inactive")
