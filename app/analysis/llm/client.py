from __future__ import annotations

import time
from collections import deque
from textwrap import dedent
from typing import Protocol

from app.core.config import Settings
from app.schemas.analysis import RatingStats, Theme


class LLMClient(Protocol):
    def summarize_insights(self, stats: RatingStats, themes: list[Theme]) -> str:
        ...


class RateLimiter:
    """Simple rate limiter using a sliding window approach."""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque[float] = deque()

    def is_allowed(self) -> bool:
        """Check if a request is allowed within the rate limit."""
        now = time.time()
        # Remove requests outside the time window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()

        if len(self.requests) >= self.max_requests:
            return False

        self.requests.append(now)
        return True

    def remaining(self) -> int:
        """Get remaining requests in the current window."""
        now = time.time()
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        return max(0, self.max_requests - len(self.requests))


class MockLLMClient:
    def __init__(self, rate_limiter: RateLimiter | None = None):
        self.rate_limiter = rate_limiter

    def summarize_insights(self, stats: RatingStats, themes: list[Theme]) -> str:
        # Check rate limit if configured
        if self.rate_limiter and not self.rate_limiter.is_allowed():
            raise RuntimeError(
                f"Rate limit exceeded. Max {self.rate_limiter.max_requests} requests per minute."
            )

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


def validate_openai_api_key(api_key: str | None) -> None:
    """Validate OpenAI API key format."""
    if not api_key:
        raise ValueError("OpenAI API key is required when LLM_PROVIDER is 'openai'")
    
    # Basic validation: OpenAI keys typically start with 'sk-'
    if not api_key.startswith("sk-"):
        raise ValueError("Invalid OpenAI API key format. Keys should start with 'sk-'")
    
    if len(api_key) < 20:
        raise ValueError("Invalid OpenAI API key format. Key appears to be too short.")


def create_llm_client(settings: Settings) -> LLMClient:
    """Create an LLM client with rate limiting and API key validation."""
    rate_limiter = None
    if settings.llm_rate_limit_rpm > 0:
        rate_limiter = RateLimiter(max_requests=settings.llm_rate_limit_rpm, window_seconds=60)

    if settings.llm_provider == "openai":
        # Validate API key before creating client
        validate_openai_api_key(settings.openai_api_key)
        # TODO: Implement OpenAI client with rate limiting
        # For now, return mock client with rate limiting
        return MockLLMClient(rate_limiter=rate_limiter)
    else:
        # Mock client with optional rate limiting for testing
        return MockLLMClient(rate_limiter=rate_limiter)

