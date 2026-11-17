from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rental import Rental


async def list_for_user(
    db: AsyncSession, user_id: int, *, limit: int = 20, offset: int = 0
) -> list[Rental]:
    result = await db.execute(
        select(Rental)
        .where(Rental.user_id == user_id)
        .order_by(Rental.id)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def list_all(
    db: AsyncSession, *, limit: int = 20, offset: int = 0
) -> list[Rental]:
    result = await db.execute(
        select(Rental).order_by(Rental.id).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def get_by_id(
    db: AsyncSession, rental_id: int, *, for_update: bool = False
) -> Rental | None:
    statement = select(Rental).where(Rental.id == rental_id)
    if for_update:
        statement = statement.with_for_update()
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def has_active_for_book(db: AsyncSession, book_id: int) -> bool:
    result = await db.execute(
        select(Rental.id)
        .where(Rental.book_id == book_id, Rental.status == "active")
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def count_active_for_user(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Rental)
        .where(Rental.user_id == user_id, Rental.status == "active")
    )
    return result.scalar_one()


async def create(db: AsyncSession, rental: Rental) -> Rental:
    db.add(rental)
    await db.flush()
    await db.refresh(rental)
    return rental
