from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, Relationship, SQLModel


class DatasetBase(SQLModel):
    name: str
    source: str = "import"
    description: str | None = None


class Dataset(DatasetBase, table=True):
    __tablename__ = "datasets"

    id: Optional[int] = Field(default=None, primary_key=True)
    total_reviews: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
    )

    reviews: list["Review"] = Relationship(back_populates="dataset")
    analysis: Optional["DatasetAnalysis"] = Relationship(back_populates="dataset")


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", nullable=False)
    product_id: str | None = None
    product_name: str | None = None
    platform: str | None = None
    rating: int = Field(default=3, ge=1, le=5)
    title: str | None = None
    body: str
    language: str | None = None
    created_at: datetime | None = None
    raw_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )

    dataset: Optional[Dataset] = Relationship(back_populates="reviews")


class DatasetAnalysis(SQLModel, table=True):
    __tablename__ = "dataset_analysis"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", unique=True, nullable=False)
    summary_text: str
    stats: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    themes: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    feature_requests: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime, nullable=False))

    dataset: Optional[Dataset] = Relationship(back_populates="analysis")

