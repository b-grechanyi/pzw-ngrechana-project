"""Create repeatable local demo accounts and books."""

import asyncio

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.core.pass_security import hash_pw
from app.models.book import Book
from app.models.user import User
from app.repositories.book_repo import get_by_isbn
from app.repositories.user_repo import get_by_email


class SeedSettings(BaseSettings):
    """Optional seed overrides, read from the root .env file."""

    model_config = SettingsConfigDict(env_file="../.env")

    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_PASSWORD: str = "demo-admin-password"
    SEED_USER_EMAIL: str = "reader@example.com"
    SEED_USER_PASSWORD: str = "demo-reader-password"


async def add_user_if_missing(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str,
) -> bool:
    existing = await get_by_email(db, email)
    if existing is not None:
        if existing.role != role:
            raise ValueError(
                f"Seed account {email!r} already exists with role "
                f"{existing.role!r}, expected {role!r}."
            )
        return False

    db.add(
        User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hash_pw(password),
            role=role,
            is_active=True,
        )
    )
    await db.flush()
    return True


async def add_book_if_missing(
    db: AsyncSession, *, title: str, author: str, isbn: str
) -> bool:
    if await get_by_isbn(db, isbn) is not None:
        return False

    db.add(Book(title=title, author=author, isbn=isbn, is_available=True))
    await db.flush()
    return True


async def seed() -> None:
    settings = SeedSettings()
    if settings.SEED_ADMIN_EMAIL.casefold() == settings.SEED_USER_EMAIL.casefold():
        raise ValueError("The seed admin and regular user must have different emails.")

    async with AsyncSessionLocal() as db:
        try:
            users_created = 0
            users_created += await add_user_if_missing(
                db,
                email=settings.SEED_ADMIN_EMAIL,
                password=settings.SEED_ADMIN_PASSWORD,
                first_name="Demo",
                last_name="Admin",
                role="admin",
            )
            users_created += await add_user_if_missing(
                db,
                email=settings.SEED_USER_EMAIL,
                password=settings.SEED_USER_PASSWORD,
                first_name="Demo",
                last_name="Reader",
                role="user",
            )

            books_created = 0
            demo_books = (
                ("The Hobbit", "J. R. R. Tolkien", "9780547928227"),
                ("Pride and Prejudice", "Jane Austen", "9780141439518"),
                ("The Little Prince", "Antoine de Saint-Exupéry", "9780156012195"),
                ("Kobzar", "Taras Shevchenko","9682156010123")
            )
            for title, author, isbn in demo_books:
                books_created += await add_book_if_missing(
                    db, title=title, author=author, isbn=isbn
                )

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    print(f"Seed complete: {users_created} user(s), {books_created} book(s) added.")


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
