from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.rental import RentalCreate, RentalResponse
from app.services.rental_service import (
    get_rental,
    list_rentals,
    rent_book,
    return_rental,
)

router = APIRouter()


@router.get("/", response_model=list[RentalResponse], summary="List rentals")
async def list_rentals_route(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[RentalResponse]:
    return await list_rentals(
        db, current_user, limit=limit, offset=offset
    )


@router.post(
    "/",
    response_model=RentalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Rent a book",
)
async def rent_book_route(
    body: RentalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentalResponse:
    return await rent_book(db, current_user, body.book_id)


@router.get(
    "/{rental_id}", response_model=RentalResponse, summary="Get rental"
)
async def get_rental_route(
    rental_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentalResponse:
    return await get_rental(db, current_user, rental_id)


@router.post(
    "/{rental_id}/return",
    response_model=RentalResponse,
    summary="Return book",
)
async def return_rental_route(
    rental_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RentalResponse:
    return await return_rental(db, current_user, rental_id)
