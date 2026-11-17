from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def has_rental_history(db: AsyncSession, user_id: int) -> bool:
    from app.models.rental import Rental

    statement = select(exists().where(Rental.user_id == user_id))
    return bool(await db.scalar(statement))


async def create(db: AsyncSession, **user_fields: object) -> User:
    user = User(**user_fields)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User, **changes: object) -> User:
    for field, value in changes.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


async def delete(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.flush()
