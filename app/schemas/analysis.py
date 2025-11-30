from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RatingStats(BaseModel):
    total_reviews: int
    average_rating: float
    rating_distribution: dict[str, int]
    positive_share: float = Field(ge=0, le=1)
    negative_share: float = Field(ge=0, le=1)


class RepresentativeReview(BaseModel):
    id: int
    rating: int
    title: str | None = None
    body_excerpt: str


class Theme(BaseModel):
    name: str
    sentiment: Literal["positive", "negative", "mixed"]
    importance: float = Field(ge=0, le=1)
    mention_count: int
    representative_reviews: list[RepresentativeReview] = Field(default_factory=list)
    summary: str | None = None
    keywords: list[str] = Field(default_factory=list)


class DatasetAnalysisPayload(BaseModel):
    dataset_id: int
    stats: RatingStats
    summary_text: str
    themes: list[Theme]
    feature_requests: list[Theme] = Field(default_factory=list)
    generated_at: datetime

