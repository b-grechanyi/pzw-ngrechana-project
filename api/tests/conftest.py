import os
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base
from app.core.deps import get_db
from app.core.pass_security import hash_pw
from app.main import create_app
from app.models.book import Book
from app.models.rental import Rental
from app.models.user import User

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://lib_user:lib_pass@localhost:5432/library_test",
)
test_url = make_url(TEST_DATABASE_URL)
if test_url.get_backend_name() != "postgresql" or not test_url.database:
    raise RuntimeError("TEST_DATABASE_URL must point to a PostgreSQL test database.")
if "test" not in test_url.database.casefold():
    raise RuntimeError("The test database name must contain 'test'.")

engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _create_test_database_if_missing():
    admin_engine = create_async_engine(
        test_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        async with admin_engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": test_url.database},
            )
            if not exists:
                database_name = test_url.database.replace('"', '""')
                await connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    finally:
        await admin_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_database():
    await _create_test_database_if_missing()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_database):
    async with engine.begin() as connection:
        tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest_asyncio.fixture
async def client(test_database):
    app = create_app()

    async def override_get_db():
        async with TestSession() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


async def _create_user(email: str, password: str, role: str = "user") -> User:
    async with TestSession() as session:
        user = User(
            first_name="Test",
            last_name="User",
            email=email,
            password_hash=hash_pw(password),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def regular_user():
    return await _create_user("marko@example.com", "marko123")


@pytest_asyncio.fixture
async def other_user():
    return await _create_user("other@example.com", "pass")


@pytest_asyncio.fixture
async def available_book():
    async with TestSession() as session:
        book = Book(
            title="Test Book",
            author="Test Author",
            isbn="9780000000001",
            is_available=True,
        )
        session.add(book)
        await session.commit()
        await session.refresh(book)
        return book


@pytest_asyncio.fixture
async def rental_fixture():
    async with TestSession() as session:
        owner = User(
            first_name="Rental",
            last_name="Owner",
            email="owner@example.com",
            password_hash=hash_pw("owner-pass"),
            role="user",
            is_active=True,
        )
        book = Book(
            title="Already Rented",
            author="Test Author",
            isbn="9780000000002",
            is_available=False,
        )
        session.add_all([owner, book])
        await session.flush()
        rented_at = datetime.now(timezone.utc)
        rental = Rental(
            user_id=owner.id,
            book_id=book.id,
            status="active",
            rented_at=rented_at,
            due_date=rented_at + timedelta(days=21),
        )
        session.add(rental)
        await session.commit()
        await session.refresh(rental)
        return rental


@pytest_asyncio.fixture
async def auth_header(client):
    async def make_header(email: str, password: str) -> dict[str, str]:
        response = await client.post(
            "/auth/login", json={"email": email, "password": password}
        )
        assert response.status_code == 200, response.text
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return make_header
