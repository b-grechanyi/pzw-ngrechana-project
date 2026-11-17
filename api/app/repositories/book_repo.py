from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.book import Book
from app.models.rental import Rental


async def list_books(
    db: AsyncSession, *, limit: int = 20, offset: int = 0
) -> list[Book]:
    result = await db.execute(
        select(Book).order_by(Book.id).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def get_by_id(
    db: AsyncSession, book_id: int, *, for_update: bool = False
) -> Book | None:
    statement = select(Book).where(Book.id == book_id)
    if for_update:
        statement = statement.with_for_update()
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_by_isbn(db: AsyncSession, isbn: str) -> Book | None:
    result = await db.execute(select(Book).where(Book.isbn == isbn))
    return result.scalar_one_or_none()


async def has_rental_history(db: AsyncSession, book_id: int) -> bool:
    statement = select(exists().where(Rental.book_id == book_id))
    return bool(await db.scalar(statement))


async def create(db: AsyncSession, **book_fields: str) -> Book:
    book = Book(**book_fields)
    db.add(book)
    await db.flush()
    await db.refresh(book)
    return book


async def update(db: AsyncSession, book: Book, **changes: str) -> Book:
    for field, value in changes.items():
        setattr(book, field, value)
    await db.flush()
    await db.refresh(book)
    return book


async def delete(db: AsyncSession, book: Book) -> None:
    await db.delete(book)
    await db.flush()
