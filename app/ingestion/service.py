from __future__ import annotations

import io
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from dateutil import parser as date_parser
from sqlmodel import Session

from app.db.models import Dataset, Review
from app.utils.text import normalize_text


@dataclass
class IngestionResult:
    imported: int
    warnings: list[str]


class IngestionService:
    COLUMN_ALIASES: dict[str, str] = {
        "product": "product_name",
        "product_name": "product_name",
        "product_title": "product_name",
        "product_id": "product_id",
        "sku": "product_id",
        "platform": "platform",
        "source": "platform",
        "rating": "rating",
        "score": "rating",
        "stars": "rating",
        "title": "title",
        "review_title": "title",
        "headline": "title",
        "body": "body",
        "review": "body",
        "content": "body",
        "text": "body",
        "language": "language",
        "lang": "language",
        "created_at": "created_at",
        "submitted_at": "created_at",
        "review_date": "created_at",
    }

    def __init__(self, session: Session):
        self.session = session

    def ingest_file(self, dataset: Dataset, payload: bytes, filename: str) -> IngestionResult:
        if not payload:
            return IngestionResult(imported=0, warnings=["Empty file"])

        extension = Path(filename).suffix.lower()
        if extension == ".csv":
            dataframe = pd.read_csv(io.BytesIO(payload))
        elif extension in {".json", ".ndjson"}:
            dataframe = self._load_json(payload)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

        normalized_df = self._normalize_columns(dataframe)
        review_models: list[Review] = []
        warnings: list[str] = []
        for row in normalized_df.to_dict(orient="records"):
            parsed = self._row_to_review(dataset_id=dataset.id, row=row)
            if not parsed:
                warnings.append("Skipped row without review body")
                continue
            review_models.append(parsed)

        if not review_models:
            return IngestionResult(imported=0, warnings=warnings or ["No valid reviews found"])

        for chunk_start in range(0, len(review_models), 500):
            chunk = review_models[chunk_start : chunk_start + 500]
            self.session.add_all(chunk)
            self.session.commit()

        return IngestionResult(imported=len(review_models), warnings=warnings)

    def _load_json(self, payload: bytes) -> pd.DataFrame:
        text = payload.decode("utf-8")
        lines = [line for line in text.strip().splitlines() if line]
        if len(lines) == 1:
            data = json.loads(lines[0])
            if isinstance(data, dict):
                if "reviews" in data:
                    data = data["reviews"]
                else:
                    data = [data]
        else:
            data = [json.loads(line) for line in lines]
        return pd.DataFrame(data)

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            col: self.COLUMN_ALIASES.get(col.lower(), col.lower())
            for col in df.columns
        }
        normalized = df.rename(columns=rename_map)
        return normalized

    def _row_to_review(self, dataset_id: int, row: dict[str, Any]) -> Review | None:
        body = normalize_text(str(row.get("body") or "")) if row.get("body") else None
        if not body:
            return None
        rating_value = self._safe_rating(row.get("rating"))
        created_at = self._safe_datetime(row.get("created_at"))
        review = Review(
            dataset_id=dataset_id,
            product_id=row.get("product_id"),
            product_name=row.get("product_name"),
            platform=row.get("platform") or "import",
            rating=rating_value,
            title=row.get("title"),
            body=body,
            language=row.get("language"),
            created_at=created_at,
            raw_metadata=row,
        )
        return review

    @staticmethod
    def _safe_rating(value: Any) -> int:
        if value is None:
            return 3
        try:
            rating = int(round(float(value)))
        except (TypeError, ValueError):
            return 3
        return max(1, min(5, rating))

    @staticmethod
    def _safe_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return date_parser.parse(str(value))
        except (ValueError, TypeError, OverflowError):
            return None

