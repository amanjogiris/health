"""Admin management routes – SUPER_ADMIN only."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user_schema import AdminCreate, UserResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/admins", tags=["Admin Management"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_admin(
    payload: AdminCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"])),
):
    """Super-Admin: create a new ADMIN account."""
    return await AuthService(db).create_admin(payload)


@router.get("", response_model=List[UserResponse])
async def list_admins(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"])),
):
    """Super-Admin: list all ADMIN accounts."""
    users = await UserRepository(db).list_by_role("admin")
    return [UserResponse.model_validate(u.to_dict()) for u in users]


@router.delete("/{admin_id}", status_code=204)
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"])),
):
    """Super-Admin: deactivate an ADMIN account."""
    repo = UserRepository(db)
    target = await repo.get_by_id(admin_id)
    if target is None:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError("Admin user")
    if target.role.value != "admin":
        from app.utils.exceptions import BusinessRuleError
        raise BusinessRuleError("User is not an admin.")
    await repo.update(admin_id, is_active=False)
