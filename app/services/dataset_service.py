from __future__ import annotations

from datetime import datetime
from typing import Iterable

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.analysis.service import ReviewAnalysisService
from app.db.models import Dataset, DatasetAnalysis, Review
from app.ingestion.service import IngestionResult, IngestionService
from app.schemas.analysis import DatasetAnalysisPayload, RatingStats, Theme
from app.schemas.datasets import DatasetCreate


class DatasetService:
    def __init__(self, session: Session, analysis_service: ReviewAnalysisService):
        self.session = session
        self.analysis_service = analysis_service

    def list_datasets(self) -> list[Dataset]:
        statement = select(Dataset).order_by(Dataset.created_at.desc())
        return list(self.session.exec(statement))

    def get_dataset(self, dataset_id: int) -> Dataset:
        return self._get_dataset_or_404(dataset_id)

    def create_dataset(self, payload: DatasetCreate) -> Dataset:
        dataset = Dataset(
            name=payload.name,
            source=payload.source,
            description=payload.description,
        )
        self.session.add(dataset)
        self.session.commit()
        self.session.refresh(dataset)
        return dataset

    def ingest_reviews(self, dataset_id: int, file_payload: bytes, filename: str) -> tuple[Dataset, IngestionResult]:
        dataset = self._get_dataset_or_404(dataset_id)
        ingestion_service = IngestionService(self.session)
        result = ingestion_service.ingest_file(dataset, payload=file_payload, filename=filename)
        dataset.total_reviews += result.imported
        dataset.updated_at = datetime.utcnow()
        self.session.add(dataset)
        self.session.commit()
        self.session.refresh(dataset)
        return dataset, result

    def get_dataset_analysis(self, dataset_id: int, force_refresh: bool = False) -> DatasetAnalysisPayload | None:
        dataset = self._get_dataset_or_404(dataset_id)
        analysis_record = self._get_analysis_record(dataset_id)
        if analysis_record and not force_refresh:
            return self._record_to_payload(dataset.id or 0, analysis_record)

        reviews = self._get_reviews(dataset_id)
        if not reviews:
            return None

        payload = self.analysis_service.run(dataset, reviews)
        if analysis_record:
            analysis_record.summary_text = payload.summary_text
            analysis_record.stats = payload.stats.model_dump()
            analysis_record.themes = [theme.model_dump() for theme in payload.themes]
            analysis_record.feature_requests = [
                theme.model_dump() for theme in payload.feature_requests
            ]
            analysis_record.generated_at = payload.generated_at
        else:
            analysis_record = DatasetAnalysis(
                dataset_id=dataset.id,
                summary_text=payload.summary_text,
                stats=payload.stats.model_dump(),
                themes=[theme.model_dump() for theme in payload.themes],
                feature_requests=[theme.model_dump() for theme in payload.feature_requests],
                generated_at=payload.generated_at,
            )
            self.session.add(analysis_record)
        self.session.commit()
        return payload

    def list_reviews(
        self,
        dataset_id: int | None = None,
        min_rating: int | None = None,
        max_rating: int | None = None,
        limit: int = 100,
    ) -> list[Review]:
        statement = select(Review).order_by(Review.created_at.desc())
        if dataset_id is not None:
            statement = statement.where(Review.dataset_id == dataset_id)
        if min_rating:
            statement = statement.where(Review.rating >= min_rating)
        if max_rating:
            statement = statement.where(Review.rating <= max_rating)
        statement = statement.limit(limit)
        return list(self.session.exec(statement))

    def _get_dataset(self, dataset_id: int) -> Dataset | None:
        statement = select(Dataset).where(Dataset.id == dataset_id)
        return self.session.exec(statement).first()

    def _get_dataset_or_404(self, dataset_id: int) -> Dataset:
        dataset = self._get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset

    def _get_analysis_record(self, dataset_id: int) -> DatasetAnalysis | None:
        statement = select(DatasetAnalysis).where(DatasetAnalysis.dataset_id == dataset_id)
        return self.session.exec(statement).first()

    def _record_to_payload(self, dataset_id: int, record: DatasetAnalysis) -> DatasetAnalysisPayload:
        stats = RatingStats.model_validate(record.stats)
        themes = [Theme.model_validate(schema) for schema in record.themes]
        feature_requests = [Theme.model_validate(schema) for schema in record.feature_requests]
        return DatasetAnalysisPayload(
            dataset_id=dataset_id,
            stats=stats,
            summary_text=record.summary_text,
            themes=themes,
            feature_requests=feature_requests,
            generated_at=record.generated_at,
        )

    def _get_reviews(self, dataset_id: int) -> Iterable[Review]:
        statement = select(Review).where(Review.dataset_id == dataset_id)
        return list(self.session.exec(statement))


