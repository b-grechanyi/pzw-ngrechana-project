from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handling import AppError
from app.core.pass_security import hash_pw
from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserUpdate


def _require_admin(actor: User) -> None:
    if actor.role != "admin":
        raise AppError("forbidden", "Only admins may manage users", 403)


async def create_user(db: AsyncSession, actor: User, data: UserCreate) -> User:
    _require_admin(actor)
    if await user_repo.get_by_email(db, str(data.email)):
        raise AppError("duplicate", "A user with this email already exists", 409)

    fields = data.model_dump(exclude={"password"})
    fields["email"] = str(data.email)
    fields["password_hash"] = hash_pw(data.password)
    try:
        return await user_repo.create(db, **fields)
    except IntegrityError as exc:
        await db.rollback()
        raise AppError("duplicate", "A user with this email already exists", 409) from exc


async def update_user(
    db: AsyncSession, actor: User, user_id: int, data: UserUpdate
) -> User:
    _require_admin(actor)
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise AppError("not_found", "User not found", 404)

    changes = data.model_dump(exclude_unset=True)
    if "password" in changes:
        changes["password_hash"] = hash_pw(changes.pop("password"))
    if "email" in changes:
        changes["email"] = str(changes["email"])
        existing = await user_repo.get_by_email(db, changes["email"])
        if existing is not None and existing.id != user.id:
            raise AppError("duplicate", "A user with this email already exists", 409)

    try:
        return await user_repo.update(db, user, **changes)
    except IntegrityError as exc:
        await db.rollback()
        raise AppError("duplicate", "A user with this email already exists", 409) from exc


async def delete_user(db: AsyncSession, actor: User, user_id: int) -> None:
    _require_admin(actor)
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise AppError("not_found", "User not found", 404)
    if await user_repo.has_rental_history(db, user.id):
        raise AppError(
            "has_rentals", "A user with rental history cannot be deleted", 409
        )
    await user_repo.delete(db, user)
