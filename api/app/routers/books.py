from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_admin
from app.models.user import User
from app.schemas.book import BookCreate, BookResponse, BookUpdate
from app.services.book_service import (
    create_book,
    delete_book,
    get_book,
    list_books,
    update_book,
)

router = APIRouter()


@router.get("/", response_model=list[BookResponse], summary="List books")
async def list_books_route(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[BookResponse]:
    return await list_books(db, limit=limit, offset=offset)


@router.get("/{book_id}", response_model=BookResponse, summary="Get book")
async def get_book_route(
    book_id: int = Path(ge=1),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    return await get_book(db, book_id)


@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create book",
)
async def create_book_route(
    body: BookCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    return await create_book(db, admin, body)


@router.patch("/{book_id}", response_model=BookResponse, summary="Update book")
async def update_book_route(
    body: BookUpdate,
    book_id: int = Path(ge=1),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    return await update_book(db, admin, book_id, body)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book",
)
async def delete_book_route(
    book_id: int = Path(ge=1),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await delete_book(db, admin, book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
