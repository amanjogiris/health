"""Authentication service – registration, login, token management."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.user_schema import UserRegister, AdminCreate, TokenResponse, UserResponse
from app.utils.exceptions import ConflictError, UnauthorizedError
from app.models.user import UserRole


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._user_repo = UserRepository(db)
        self._patient_repo = PatientRepository(db)

    async def register(self, payload: UserRegister) -> TokenResponse:
        """Register a new PATIENT account and return a token."""
        existing = await self._user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictError("Email is already registered.")

        user = await self._user_repo.create(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role="patient",          # always patient for public registration
            mobile_no=payload.mobile_no,
            address=payload.address,
        )

        # Automatically create a patient profile
        await self._patient_repo.create(user_id=user.id)

        token = create_access_token(user.id, user.role.value)
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user.to_dict()),
        )

    async def create_admin(self, payload: AdminCreate) -> UserResponse:
        """Create an ADMIN account (callable by SUPER_ADMIN only)."""
        existing = await self._user_repo.get_by_email(payload.email)
        if existing:
            raise ConflictError("Email is already registered.")

        user = await self._user_repo.create(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role="admin",
            mobile_no=payload.mobile_no,
        )
        return UserResponse.model_validate(user.to_dict())

    async def login(self, email: str, password: str) -> TokenResponse:
        """Validate credentials and return a token."""
        user = await self._user_repo.get_by_email(email)
        if not user or not user.verify_password(password):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive.")

        from datetime import datetime

        await self._user_repo.update(user.id, last_login=datetime.utcnow())

        token = create_access_token(user.id, user.role.value)
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user.to_dict()),
        )
