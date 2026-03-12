"""Admin management routes – SUPER_ADMIN only."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user_schema import AdminCreate, UserResponse
from app.schemas.pagination import PaginatedResponse
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


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_admins(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(["SUPER_ADMIN"])),
):
    """Super-Admin: list all ADMIN accounts."""
    count_result = await db.execute(
        select(func.count()).select_from(User).where(
            User.role == UserRole("admin"), User.is_active == True
        )
    )
    total = count_result.scalar_one()
    users = await UserRepository(db).list_by_role("admin", skip=skip, limit=limit)
    return PaginatedResponse(
        items=[UserResponse.model_validate(u.to_dict()) for u in users],
        total=total,
        skip=skip,
        limit=limit,
    )


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
