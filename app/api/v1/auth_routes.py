"""Auth routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, blacklist_token
from app.db.session import get_db
from app.schemas.user_schema import UserRegister, TokenResponse, UserResponse, LogoutResponse
from app.services.auth_service import AuthService
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    service = AuthService(db)
    return await service.register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Login and receive a JWT token.

    Accepts OAuth2 ``application/x-www-form-urlencoded`` with fields
    ``username`` (treated as email) and ``password``.
    """
    service = AuthService(db)
    return await service.login(form_data.username, form_data.password)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
):
    """Invalidate the current bearer token."""
    blacklist_token(token)
    return LogoutResponse()


@router.get("/profile", response_model=UserResponse)
async def profile(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user.to_dict())
