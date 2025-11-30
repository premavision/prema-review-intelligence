from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.analysis.classical import (
    compute_rating_stats,
    detect_feature_requests,
    extract_themes,
)
from app.analysis.llm.client import LLMClient
from app.db.models import Dataset, Review
from app.schemas.analysis import DatasetAnalysisPayload


class ReviewAnalysisService:
    def __init__(self, llm_client: LLMClient, max_themes: int = 6):
        self.llm_client = llm_client
        self.max_themes = max_themes

    def run(self, dataset: Dataset, reviews: Iterable[Review]) -> DatasetAnalysisPayload:
        review_list = list(reviews)
        stats = compute_rating_stats(review_list)
        themes = extract_themes(review_list, self.max_themes)
        feature_requests = detect_feature_requests(themes)
        summary_text = self.llm_client.summarize_insights(stats, themes)
        payload = DatasetAnalysisPayload(
            dataset_id=dataset.id or 0,
            stats=stats,
            summary_text=summary_text,
            themes=themes,
            feature_requests=feature_requests,
            generated_at=datetime.utcnow(),
        )
        return payload

