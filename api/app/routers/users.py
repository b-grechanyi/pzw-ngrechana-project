from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.models.user import User
from app.repositories.user_repo import get_all
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
async def list_users(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    return await get_all(db)
