from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handling import AppError
from app.models.book import Book
from app.models.user import User
from app.repositories import book_repo
from app.schemas.book import BookCreate, BookUpdate


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise AppError("forbidden", "Only admins may manage books", 403)


async def list_books(
    db: AsyncSession, *, limit: int = 20, offset: int = 0
) -> list[Book]:
    return await book_repo.list_books(db, limit=limit, offset=offset)


async def get_book(db: AsyncSession, book_id: int) -> Book:
    book = await book_repo.get_by_id(db, book_id)
    if book is None:
        raise AppError("not_found", "Book not found", 404)
    return book


async def create_book(db: AsyncSession, actor: User, data: BookCreate) -> Book:
    _require_admin(actor)
    if await book_repo.get_by_isbn(db, data.isbn):
        raise AppError("duplicate", "A book with this ISBN already exists", 409)

    try:
        return await book_repo.create(db, **data.model_dump())
    except IntegrityError as exc:
        await db.rollback()
        raise AppError("duplicate", "A book with this ISBN already exists", 409) from exc


async def update_book(
    db: AsyncSession, actor: User, book_id: int, data: BookUpdate
) -> Book:
    _require_admin(actor)
    book = await get_book(db, book_id)
    changes = data.model_dump(exclude_unset=True)

    if "isbn" in changes:
        existing = await book_repo.get_by_isbn(db, changes["isbn"])
        if existing is not None and existing.id != book.id:
            raise AppError("duplicate", "A book with this ISBN already exists", 409)

    try:
        return await book_repo.update(db, book, **changes)
    except IntegrityError as exc:
        await db.rollback()
        raise AppError("duplicate", "A book with this ISBN already exists", 409) from exc


async def delete_book(db: AsyncSession, actor: User, book_id: int) -> None:
    _require_admin(actor)
    book = await get_book(db, book_id)
    if await book_repo.has_rental_history(db, book.id):
        raise AppError(
            "has_rentals", "A book with rental history cannot be deleted", 409
        )
    await book_repo.delete(db, book)
