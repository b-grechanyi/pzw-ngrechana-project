from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class RentalCreate(BaseModel):
    """Input for starting a rental; the authenticated user is assigned by the API."""
    book_id: int = Field(gt=0)


class RentalResponse(BaseModel):
    """Public rental data. No password or other private user data is included."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    status: Literal["active", "returned"]
    rented_at: datetime
    due_date: datetime
