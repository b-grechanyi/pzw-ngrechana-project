from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookCreate(BaseModel):
    """Fields an administrator may supply when adding a book."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)
    isbn: str = Field(min_length=1, max_length=20)


class BookUpdate(BaseModel):
    """Optional fields for a partial book update; null values are rejected."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    author: str | None = Field(default=None, min_length=1, max_length=120)
    isbn: str | None = Field(default=None, min_length=1, max_length=20)

    @model_validator(mode="after")
    def require_at_least_one_non_null_change(self) -> "BookUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Updated fields cannot be null")
        return self


class BookResponse(BaseModel):
    """Public book data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    is_available: bool
