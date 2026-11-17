import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handling import AppError
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.pass_security import verify_password
from app.repositories.user_repo import get_by_email, get_by_id


def _tokens(user_id: int, role: str) -> dict[str, str]:
    return {
        "access_token": create_access_token(user_id, role),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


async def login(db: AsyncSession, email: str, password: str) -> tuple[object, dict]:
    user = await get_by_email(db, email)

    # Use the same public error for unknown email and wrong password.
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("invalid_credentials", "Invalid email or password", 401)

    if not user.is_active:
        raise AppError("invalid_credentials", "Invalid email or password", 401)

    return user, _tokens(user.id, user.role)


async def refresh(db: AsyncSession, raw_token: str) -> dict[str, str]:
    try:
        payload = decode_token(raw_token)
    except jwt.ExpiredSignatureError as exc:
        raise AppError("token_expired", "Refresh token has expired", 401) from exc
    except jwt.InvalidTokenError as exc:
        raise AppError("invalid_token", "Invalid refresh token", 401) from exc

    if payload.get("type") != "refresh":
        raise AppError("invalid_token", "Refresh token required", 401)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AppError("invalid_token", "Invalid token subject", 401) from exc

    user = await get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AppError("invalid_credentials", "Invalid credentials", 401)

    return _tokens(user.id, user.role)