from collections.abc import AsyncGenerator
import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.error_handling import AppError
from app.core.jwt import decode_token
from app.models.user import User
from app.repositories.user_repo import get_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db),) -> User:
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