from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .analysis import DatasetAnalysisPayload


class DatasetCreate(BaseModel):
    name: str
    source: str = "import"
    description: str | None = None


class DatasetRead(DatasetCreate):
    id: int
    total_reviews: int
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    datasets: list[DatasetRead]


class DatasetSummaryResponse(BaseModel):
    dataset: DatasetRead
    analysis: DatasetAnalysisPayload | None = None


class DatasetIngestionResponse(BaseModel):
    dataset: DatasetRead
    imported_reviews: int
    warnings: list[str] = []
    extra: dict[str, Any] = {}
