from __future__ import annotations

from textwrap import dedent
from typing import Protocol

from app.core.config import Settings
from app.schemas.analysis import RatingStats, Theme


class LLMClient(Protocol):
    def summarize_insights(self, stats: RatingStats, themes: list[Theme]) -> str:
        ...


class MockLLMClient:
    def summarize_insights(self, stats: RatingStats, themes: list[Theme]) -> str:
        positive = ", ".join(
            theme.name for theme in themes if theme.sentiment == "positive"
        ) or "a few highlights"
        negative = ", ".join(
            theme.name for theme in themes if theme.sentiment == "negative"
        ) or "a handful of friction points"
        mixed = ", ".join(
            theme.name for theme in themes if theme.sentiment == "mixed"
        ) or "some nuanced trade-offs"
        summary = dedent(
            f"""
            Across {stats.total_reviews} reviews customers rate the experience
            {stats.average_rating}/5 on average. Promoters highlight {positive},
            while detractors complain about {negative}. Teams should also pay attention to {mixed}
            which appears in both positive and negative contexts.
            """
        ).strip()
        return " ".join(summary.split())


def create_llm_client(settings: Settings) -> LLMClient:
    # Placeholder for integrating real providers (OpenAI, Anthropic, etc.)
    return MockLLMClient()

