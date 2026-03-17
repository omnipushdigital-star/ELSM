from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.models import User, UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


def require_roles(*roles: UserRole):
    """Role-based access control dependency factory."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}",
            )
        return current_user
    return role_checker


# ─── Shorthand role dependencies ────────────────────────────────────────────

def get_super_admin(user: User = Depends(require_roles(UserRole.SUPER_ADMIN))) -> User:
    return user

def get_bsnl_or_above(user: User = Depends(
    require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN)
)) -> User:
    return user

def get_officer_or_above(user: User = Depends(
    require_roles(UserRole.SUPER_ADMIN, UserRole.BSNL_ADMIN, UserRole.NODAL_OFFICER)
)) -> User:
    return user

def get_any_authenticated(user: User = Depends(get_current_user)) -> User:
    return user
