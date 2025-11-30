from datetime import datetime

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    dataset_id: int
    product_id: str | None = None
    product_name: str | None = None
    platform: str | None = "import"
    rating: int = Field(ge=1, le=5)
    title: str | None = None
    body: str
    language: str | None = None
    created_at: datetime | None = None
    raw_metadata: dict[str, object] | None = None


class ReviewCreate(ReviewBase):
    pass


class ReviewRead(ReviewBase):
    id: int

