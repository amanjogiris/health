"""Asynchronous database engine and session for the app.

This module provides an async engine and `async_sessionmaker` for use in
FastAPI dependencies. It matches the async URL configured in
`alembic.ini` (e.g. `postgresql+asyncpg://...`).
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base

# Replace with your real URL or keep alembic.ini as single source of truth.
DATABASE_URL = "postgresql+asyncpg://postgres:Cancer%40%232626@localhost:5432/health_db"


engine: AsyncEngine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
