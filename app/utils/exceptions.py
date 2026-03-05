"""Custom exception classes and global exception handlers."""
from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status


class AppException(Exception):
    """Base application exception."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, f"{resource} not found.")


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists.") -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Forbidden.") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Unauthorized.") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


class BusinessRuleError(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)


# ─── handlers ──────────────────────────────────────────────────────────────


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # exc.body may be raw bytes (e.g. form-encoded payloads from Swagger UI)
    # which are not JSON-serialisable; decode safely.
    body = exc.body
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", errors="replace")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )
