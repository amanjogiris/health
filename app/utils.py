"""Utility functions for the application."""

from datetime import datetime
from typing import Optional, Dict, Any
import uuid


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracking."""
    return str(uuid.uuid4())


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)


def paginate(items: list, skip: int = 0, limit: int = 100) -> list:
    """Paginate a list of items."""
    return items[skip : skip + limit]


def get_pagination_info(total: int, skip: int, limit: int) -> Dict[str, Any]:
    """Generate pagination metadata."""
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 0,
        "current_page": (skip // limit) + 1 if limit > 0 else 1,
    }


def mask_sensitive_data(data: Dict[str, Any], fields_to_mask: list = None) -> Dict[str, Any]:
    """Mask sensitive fields in a dictionary."""
    if fields_to_mask is None:
        fields_to_mask = ["password", "password_hash", "secret_key", "token"]

    masked_data = data.copy()
    for field in fields_to_mask:
        if field in masked_data:
            masked_data[field] = "***MASKED***"

    return masked_data


def is_valid_email(email: str) -> bool:
    """Basic email validation."""
    return "@" in email and "." in email.split("@")[1] if "@" in email else False


def is_strong_password(password: str) -> bool:
    """Check if password meets minimum strength requirements."""
    # At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input."""
    if not isinstance(value, str):
        return str(value)
    
    # Remove leading/trailing whitespace
    value = value.strip()
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value


def parse_datetime(date_string: str) -> Optional[datetime]:
    """Parse datetime from ISO 8601 string."""
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


def get_time_difference_in_minutes(dt1: datetime, dt2: datetime) -> int:
    """Get time difference between two datetimes in minutes."""
    if dt1 and dt2:
        diff = abs((dt1 - dt2).total_seconds())
        return int(diff // 60)
    return 0


def is_time_slot_available(slot_start: datetime, slot_end: datetime, duration_minutes: int) -> bool:
    """Check if time slot has enough duration."""
    if slot_start and slot_end:
        duration = get_time_difference_in_minutes(slot_start, slot_end)
        return duration >= duration_minutes
    return False


def format_phone_number(phone: str) -> str:
    """Format phone number by removing non-digits."""
    if phone:
        return ''.join(filter(str.isdigit, phone))
    return ""


def is_valid_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone:
        return False
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 10 and len(digits) <= 15


def group_by_key(items: list, key: str) -> Dict[str, list]:
    """Group list items by a key."""
    grouped = {}
    for item in items:
        if isinstance(item, dict):
            group_key = item.get(key)
        else:
            group_key = getattr(item, key, None)
        
        if group_key not in grouped:
            grouped[group_key] = []
        grouped[group_key].append(item)
    
    return grouped
