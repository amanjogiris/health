"""Asynchronous database engine and session for the app.

This module provides an async engine and `async_sessionmaker` for use in
FastAPI dependencies. It matches the async URL configured in
`alembic.ini` (e.g. `postgresql+asyncpg://...`).
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Build the URL from individual env vars so special characters in passwords
# (e.g. @, #, %) are safely percent-encoded and never break URL parsing.
_user = os.getenv("DB_USER", "postgres")
_password = quote_plus(os.getenv("DB_PASSWORD", ""))
_host = os.getenv("DB_HOST", "localhost")
_port = os.getenv("DB_PORT", "5432")
_name = os.getenv("DB_NAME", "health_db")

DATABASE_URL = f"postgresql+asyncpg://{_user}:{_password}@{_host}:{_port}/{_name}"


engine: AsyncEngine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
