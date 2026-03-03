"""Reusable SQLAlchemy column mixins for the health_app models."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, func
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class TimestampMixin:
    """Adds `created_at` and `updated_at` columns with DB-side defaults."""

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


@declarative_mixin
class SoftDeleteMixin:
    """Adds a simple `is_active` flag instead of hard deletes."""

    is_active = Column(Boolean, default=True, nullable=False)


__all__ = ["TimestampMixin", "SoftDeleteMixin"]
