from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from app.db.models import Review
from app.schemas.analysis import RatingStats, RepresentativeReview, Theme
from app.utils.text import excerpt, normalize_text

STOPWORDS = set(ENGLISH_STOP_WORDS) | {
    "product",
    "amazon",
    "shopify",
    "item",
    "customer",
    "review",
    "reviews",
    "purchase",
    "use",
    "used",
    "using",
    "also",
    "get",
    "got",
    "one",
    "really",
    "would",
    "could",
    "still",
}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z']+")
FEATURE_REQUEST_KEYWORDS = {"wish", "hope", "should", "add", "feature", "request", "need", "needs"}


def compute_rating_stats(reviews: Iterable[Review]) -> RatingStats:
    reviews_list = list(reviews)
    total = len(reviews_list)
    if total == 0:
        return RatingStats(
            total_reviews=0,
            average_rating=0,
            rating_distribution={str(idx): 0 for idx in range(1, 6)},
            positive_share=0,
            negative_share=0,
        )

    distribution = Counter(str(min(5, max(1, review.rating or 0))) for review in reviews_list)
    for rating in range(1, 6):
        distribution.setdefault(str(rating), 0)
    average_rating = sum(review.rating or 0 for review in reviews_list) / total
    promoters = sum(1 for review in reviews_list if (review.rating or 0) >= 4)
    detractors = sum(1 for review in reviews_list if (review.rating or 0) <= 2)
    return RatingStats(
        total_reviews=total,
        average_rating=round(average_rating, 2),
        rating_distribution=dict(sorted(distribution.items())),
        positive_share=round(promoters / total, 3),
        negative_share=round(detractors / total, 3),
    )


@dataclass
class ThemeAccumulator:
    mention_count: int
    review_ids: set[int]
    ratings: list[int]
    examples: list[Review]
    keywords: set[str]


def extract_themes(reviews: Iterable[Review], max_themes: int) -> list[Theme]:
    reviews_list = [review for review in reviews if review.body]
    if not reviews_list:
        return []
    total_reviews = len(reviews_list)
    theme_map: dict[str, ThemeAccumulator] = {}
    for review in reviews_list:
        tokens = tokenize(review.body)
        if not tokens:
            continue
        candidate_terms = set(tokens)
        bigrams = {" ".join(pair) for pair in zip(tokens, tokens[1:]) if len(pair) == 2}
        candidate_terms |= {gram for gram in bigrams if len(gram.split()) > 1}
        for term in candidate_terms:
            theme = theme_map.setdefault(
                term,
                ThemeAccumulator(
                    mention_count=0,
                    review_ids=set(),
                    ratings=[],
                    examples=[],
                    keywords=set(),
                ),
            )
            theme.mention_count += 1
            if review.id is not None:
                theme.review_ids.add(review.id)
            theme.ratings.append(review.rating or 0)
            if len(theme.examples) < 5:
                theme.examples.append(review)
            theme.keywords.update(term.split())

    sorted_terms = sorted(
        theme_map.items(),
        key=lambda item: (item[1].mention_count / total_reviews, sum(item[1].ratings)),
        reverse=True,
    )
    top_terms = sorted_terms[:max_themes * 2]
    themes: list[Theme] = []
    for term, acc in top_terms:
        mention_share = acc.mention_count / total_reviews
        avg_rating = sum(acc.ratings) / len(acc.ratings)
        sentiment = classify_sentiment(avg_rating)
        representative_reviews = [
            RepresentativeReview(
                id=review.id or 0,
                rating=review.rating or 0,
                title=review.title,
                body_excerpt=excerpt(review.body),
            )
            for review in acc.examples[:3]
            if review.id is not None
        ]
        theme = Theme(
            name=term.title(),
            sentiment=sentiment,
            importance=round(mention_share, 3),
            mention_count=len(acc.review_ids) or acc.mention_count,
            representative_reviews=representative_reviews,
            keywords=sorted(acc.keywords),
        )
        themes.append(theme)

    themes = deduplicate_themes(themes, max_themes)
    return themes[:max_themes]


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text.lower())
    tokens = [token for token in TOKEN_RE.findall(normalized) if len(token) > 2]
    filtered = [token for token in tokens if token not in STOPWORDS]
    return filtered


def classify_sentiment(avg_rating: float) -> str:
    if avg_rating >= 4:
        return "positive"
    if avg_rating <= 2.5:
        return "negative"
    return "mixed"


def deduplicate_themes(themes: list[Theme], limit: int) -> list[Theme]:
    unique: list[Theme] = []
    seen_keywords: set[str] = set()
    for theme in themes:
        key = " ".join(sorted(theme.keywords))
        if not key:
            continue
        if key in seen_keywords:
            continue
        seen_keywords.add(key)
        unique.append(theme)
        if len(unique) >= limit:
            break
    return unique


def detect_feature_requests(themes: list[Theme]) -> list[Theme]:
    requests: list[Theme] = []
    for theme in themes:
        signal = any(keyword.lower() in FEATURE_REQUEST_KEYWORDS for keyword in theme.keywords)
        if signal or "feature" in theme.name.lower():
            requests.append(theme)
    return requests

