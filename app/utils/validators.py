"""Input validators shared across the application."""
from __future__ import annotations

from datetime import datetime


def slot_times_are_valid(start: datetime, end: datetime) -> bool:
    """Return True if end is strictly after start."""
    return end > start


def password_is_strong(password: str) -> bool:
    """Return True if password meets minimum strength requirements."""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_digit
