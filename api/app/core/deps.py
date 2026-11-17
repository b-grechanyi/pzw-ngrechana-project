from collections.abc import AsyncGenerator, Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.error_handling import AppError
from app.core.jwt import decode_token
from app.models.user import User
from app.repositories.user_repo import get_by_id

bearer_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise AppError("token_expired", "Token has expired", 401) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError("invalid_token", "Invalid token", 401) from exc

    if payload.get("type") != "access":
        raise AppError("invalid_token", "Access token required", 401)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AppError("invalid_token", "Invalid token subject", 401) from exc

    user = await get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AppError("invalid_credentials", "Invalid credentials", 401)

    return user


def require_role(required_role: str) -> Callable:
    """Build a dependency that allows only users with the given role."""

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role:
            raise AppError("forbidden", "Insufficient permissions", 403)
        return user

    return role_checker


require_admin = require_role("admin")
