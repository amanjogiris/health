"""User repository – data access for the User model."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        name: str,
        email: str,
        password: str,
        role: str = "patient",
        **kwargs,
    ) -> User:
        user = User(name=name, email=email, role=UserRole(role), **kwargs)
        user.set_password(password)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        for k, v in kwargs.items():
            if hasattr(user, k) and v is not None:
                setattr(user, k, v)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = (
            select(User)
            .where(User.role == UserRole(role), User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
