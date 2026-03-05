"""FastAPI dependency factories for authentication and authorisation."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ─── simple in-process token blacklist ───────────────────────────────────────
# Replace with Redis in production for multi-process deployments.
_token_blacklist: set[str] = set()


def blacklist_token(token: str) -> None:
    _token_blacklist.add(token)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the current authenticated user from the Bearer token."""
    if token in _token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated. Please log in again.",
        )

    try:
        payload = decode_access_token(token)
        user_id: int = int(payload["sub"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.repositories.user_repository import UserRepository

    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


def require_roles(*roles: str):
    """Return a dependency that asserts the current user has one of *roles*.

    Comparison is case-insensitive so callers may pass ``"ADMIN"`` or
    ``"admin"`` interchangeably.
    """
    normalised = {r.lower() for r in roles}

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value.lower() not in normalised:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _check


# Convenience alias that accepts a list  — require_role(["ADMIN", "SUPER_ADMIN"])
def require_role(roles: list[str]):
    """Alias for :func:`require_roles` that accepts a list instead of *args."""
    return require_roles(*roles)
