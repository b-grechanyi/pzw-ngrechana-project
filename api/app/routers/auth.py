from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import login, refresh

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="Login")
async def login_route(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    user, tokens = await login(db, body.email, body.password)
    return {"user": user, **tokens}


@router.post("/refresh", response_model=TokenResponse, summary="Refresh tokens")
async def refresh_route(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await refresh(db, body.refresh_token)


@router.get("/me", response_model=UserResponse, summary="Current user")
async def me_route(user: User = Depends(get_current_user)):
    return user