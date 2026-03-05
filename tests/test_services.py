"""Unit tests for service layer (mocked repositories)."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.user_schema import UserRegister
from app.services.auth_service import AuthService
from app.utils.exceptions import ConflictError, UnauthorizedError


class _FakeUser:
    id = 1
    role = MagicMock()
    is_active = True

    def verify_password(self, pwd: str) -> bool:
        return pwd == "correct"

    def to_dict(self):
        return {
            "id": 1, "name": "Test", "email": "t@t.com",
            "role": "patient", "mobile_no": None, "address": None,
            "is_verified": False, "is_active": True,
            "last_login": None, "created_at": None,
        }


_fake_user = _FakeUser()
_fake_user.role.value = "patient"


@pytest.mark.asyncio
async def test_auth_service_register_conflict():
    db = AsyncMock()
    service = AuthService(db)

    with patch.object(service._user_repo, "get_by_email", return_value=_fake_user):
        with pytest.raises(ConflictError):
            await service.register(
                UserRegister(
                    name="X", email="t@t.com", password="Password1", role="patient"
                )
            )


@pytest.mark.asyncio
async def test_auth_service_login_bad_creds():
    db = AsyncMock()
    service = AuthService(db)

    with patch.object(service._user_repo, "get_by_email", return_value=None):
        with pytest.raises(UnauthorizedError):
            await service.login("x@x.com", "WrongPass1")


@pytest.mark.asyncio
async def test_slot_service_overlap_raises():
    from app.schemas.slot_schema import SlotCreate
    from app.services.slot_service import SlotService
    from app.utils.exceptions import BusinessRuleError
    from datetime import datetime, timezone, timedelta

    db = AsyncMock()
    service = SlotService(db)

    start = datetime.now(timezone.utc) + timedelta(hours=1)
    end = start + timedelta(hours=1)

    with patch.object(service._repo, "has_overlap", return_value=True):
        with pytest.raises(BusinessRuleError):
            await service.create(
                SlotCreate(doctor_id=1, clinic_id=1, start_time=start, end_time=end)
            )
