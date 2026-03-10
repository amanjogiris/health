"""Auth routes."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, blacklist_token
from app.db.session import get_db
from app.schemas.user_schema import UserRegister, TokenResponse, UserResponse, LogoutResponse, UserProfileUpdate, ChangePassword
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


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the authenticated user's own name, mobile number, and address."""
    if payload.name is not None:
        current_user.name = payload.name
    if payload.mobile_no is not None:
        current_user.mobile_no = payload.mobile_no
    if payload.address is not None:
        current_user.address = payload.address
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user.to_dict())


@router.patch("/password", status_code=200)
async def change_password(
    payload: ChangePassword,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the authenticated user's password."""
    if not current_user.verify_password(payload.current_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    current_user.set_password(payload.new_password)
    db.add(current_user)
    await db.commit()
    return {"message": "Password updated successfully."}


@router.post("/profile/image", response_model=UserResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a profile photo. Accepts image/jpeg, image/png, image/webp."""
    allowed = {'image/jpeg', 'image/png', 'image/webp'}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail='Only JPEG, PNG, or WebP images are allowed.')

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in (file.filename or '') else 'jpg'
    filename = f'{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}'
    # Path(__file__) = .../app/api/v1/auth_routes.py  → 4 parents up = project root
    upload_dir = Path(__file__).resolve().parent.parent.parent.parent / 'static' / 'uploads'
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / filename
    contents = await file.read()
    with open(file_path, 'wb') as f:
        f.write(contents)

    current_user.image = f'/static/uploads/{filename}'
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user.to_dict())
