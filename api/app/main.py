from fastapi import FastAPI
from app.core.config import settings
from app.core.error_handling import AppError, app_error_handler, validation_error_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from app.routers import auth, books, health, rentals, users

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url="/docs" if settings.ENV == "dev" else None,
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(books.router, prefix="/books", tags=["books"])
    app.include_router(rentals.router, prefix="/rentals", tags=["rentals"])

    return app

app = create_app()
