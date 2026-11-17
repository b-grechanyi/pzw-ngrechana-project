from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.error_handling import AppError
from app.models.book import Book
from app.models.rental import Rental
from app.models.user import User
from app.repositories import book_repo, rental_repo

DEFAULT_RENTAL_DAYS = 21
MAX_ACTIVE_RENTALS = 5


async def list_rentals(
    db: AsyncSession,
    actor: User,
    *,
    limit: int = 20,
    offset: int = 0,
) -> list[Rental]:
    if actor.role == "admin":
        return await rental_repo.list_all(db, limit=limit, offset=offset)
    return await rental_repo.list_for_user(
        db, actor.id, limit=limit, offset=offset
    )


async def get_rental(db: AsyncSession, actor: User, rental_id: int) -> Rental:
    rental = await rental_repo.get_by_id(db, rental_id)
    if rental is None:
        raise AppError("not_found", "Rental not found", 404)
    if actor.role != "admin" and rental.user_id != actor.id:
        raise AppError("forbidden", "You cannot access this rental", 403)
    return rental


async def rent_book(
    db: AsyncSession,
    actor: User,
    book_id: int,
    *,
    rental_days: int = DEFAULT_RENTAL_DAYS,
) -> Rental:
    # Lock the book row so simultaneous requests cannot both rent it.
    book = await book_repo.get_by_id(db, book_id, for_update=True)
    if book is None:
        raise AppError("not_found", "Book not found", 404)
    if not book.is_available or await rental_repo.has_active_for_book(db, book.id):
        raise AppError("book_unavailable", "This book is already rented", 409)
    active_rentals = await rental_repo.count_active_for_user(db, actor.id)
    if active_rentals >= MAX_ACTIVE_RENTALS:
        raise AppError(
            "rental_limit_reached",
            f"You cannot have more than {MAX_ACTIVE_RENTALS} active rentals",
            409,
        )

    rented_at = datetime.now(timezone.utc)
    rental = Rental(
        user_id=actor.id,
        book_id=book.id,
        status="active",
        rented_at=rented_at,
        due_date=rented_at + timedelta(days=rental_days),
    )
    book.is_available = False
    return await rental_repo.create(db, rental)


async def return_rental(db: AsyncSession, actor: User, rental_id: int) -> Rental:
    # Read first to find the book, then acquire locks in the same book-first
    # order as rent_book. Re-read the rental under lock before changing state.
    rental = await rental_repo.get_by_id(db, rental_id)
    if rental is None:
        raise AppError("not_found", "Rental not found", 404)
    if actor.role != "admin" and rental.user_id != actor.id:
        raise AppError("forbidden", "You cannot return this rental", 403)
    if rental.status != "active":
        raise AppError("already_returned", "This rental has already been returned", 409)

    book = await book_repo.get_by_id(db, rental.book_id, for_update=True)
    if book is None:
        raise AppError("not_found", "Book not found", 404)

    rental = await rental_repo.get_by_id(db, rental_id, for_update=True)
    if rental is None:
        raise AppError("not_found", "Rental not found", 404)
    if actor.role != "admin" and rental.user_id != actor.id:
        raise AppError("forbidden", "You cannot return this rental", 403)
    if rental.status != "active":
        raise AppError("already_returned", "This rental has already been returned", 409)

    rental.status = "returned"
    book.is_available = True
    await db.flush()
    await db.refresh(rental)
    return rental
