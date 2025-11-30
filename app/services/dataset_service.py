from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.analysis.service import ReviewAnalysisService
from app.core.config import settings
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
        ingestion_service = IngestionService(self.session, max_rows=settings.max_ingestion_rows)
        result = ingestion_service.ingest_file(dataset, payload=file_payload, filename=filename)
        
        # Update dataset metadata only if reviews were actually imported
        if result.imported > 0:
            dataset.total_reviews += result.imported
            dataset.updated_at = datetime.utcnow()
            self.session.add(dataset)
            
            # Invalidate analysis cache when new reviews are ingested
            self._invalidate_analysis_cache(dataset_id)
        
        self.session.commit()
        self.session.refresh(dataset)
        return dataset, result

    def get_dataset_analysis(self, dataset_id: int, force_refresh: bool = False) -> DatasetAnalysisPayload | None:
        dataset = self._get_dataset_or_404(dataset_id)
        analysis_record = self._get_analysis_record(dataset_id)
        
        # Check if cache should be invalidated
        should_refresh = force_refresh or self._is_cache_stale(dataset, analysis_record)
        
        if analysis_record and not should_refresh:
            return self._record_to_payload(dataset.id or 0, analysis_record)

        reviews = self._get_reviews(dataset_id)
        if not reviews:
            return None

        payload = self.analysis_service.run(dataset, reviews)
        if analysis_record:
            # Update existing analysis record
            analysis_record.summary_text = payload.summary_text
            analysis_record.stats = payload.stats.model_dump()
            analysis_record.themes = [theme.model_dump() for theme in payload.themes]
            analysis_record.feature_requests = [
                theme.model_dump() for theme in payload.feature_requests
            ]
            analysis_record.generated_at = payload.generated_at
        else:
            # Create new analysis record
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

    def _invalidate_analysis_cache(self, dataset_id: int) -> None:
        """Invalidate (delete) the analysis cache for a dataset."""
        analysis_record = self._get_analysis_record(dataset_id)
        if analysis_record:
            self.session.delete(analysis_record)
            # Note: commit happens in the caller (ingest_reviews)

    def _is_cache_stale(
        self, dataset: Dataset, analysis_record: DatasetAnalysis | None
    ) -> bool:
        """
        Check if the analysis cache is stale based on:
        1. TTL (time to live) - if analysis is older than configured TTL
        2. Dataset updates - if dataset was updated after analysis was generated
        """
        if not analysis_record:
            return True

        now = datetime.utcnow()
        
        # Check TTL: if analysis is older than TTL, consider it stale
        ttl_delta = timedelta(minutes=settings.summary_cache_ttl_minutes)
        if analysis_record.generated_at + ttl_delta < now:
            return True

        # Check if dataset was updated after analysis was generated
        # This handles the case where reviews were ingested but cache wasn't invalidated
        if dataset.updated_at and analysis_record.generated_at:
            if dataset.updated_at > analysis_record.generated_at:
                return True

        return False


