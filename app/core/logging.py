"""Structured application logging configuration."""
from __future__ import annotations

import logging
import sys

from app.config import settings


def configure_logging() -> None:
    """Configure root logger with structured formatting."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%dT%H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt=date_fmt,
        stream=sys.stdout,
    )

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
