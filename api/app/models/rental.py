from typing import TYPE_CHECKING
import datetime as dt
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from sqlalchemy import CheckConstraint


if TYPE_CHECKING:
    from .book import Book
    from .user import User

class Rental(Base):
    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    rented_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="rentals")
    book: Mapped["Book"] = relationship(back_populates="rentals")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'returned')", name="ck_rental_status"),
    )
