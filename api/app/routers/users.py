from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.models.user import User
from app.repositories.user_repo import get_all
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_user, delete_user, update_user

router = APIRouter()
AdminUser = Annotated[User, Depends(require_admin)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[UserResponse], summary="List users")
async def list_users(
    _admin: AdminUser,
    db: DatabaseSession,
) -> list[User]:
    return await get_all(db)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
)
async def create_user_route(
    body: UserCreate,
    admin: AdminUser,
    db: DatabaseSession,
) -> User:
    return await create_user(db, admin, body)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user_route(
    body: UserUpdate,
    user_id: Annotated[int, Path(ge=1)],
    admin: AdminUser,
    db: DatabaseSession,
) -> User:
    return await update_user(db, admin, user_id, body)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
async def delete_user_route(
    user_id: Annotated[int, Path(ge=1)],
    admin: AdminUser,
    db: DatabaseSession,
) -> Response:
    await delete_user(db, admin, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
