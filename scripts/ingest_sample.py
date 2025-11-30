from __future__ import annotations

import argparse
from pathlib import Path

from sqlmodel import Session

from app.analysis.llm.client import create_llm_client
from app.analysis.service import ReviewAnalysisService
from app.core.config import settings
from app.db.base import engine, init_db
from app.schemas.datasets import DatasetCreate
from app.services.dataset_service import DatasetService


def main(path: str) -> None:
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise SystemExit(f"File not found: {file_path}")

    init_db()
    llm_client = create_llm_client(settings)
    analysis_service = ReviewAnalysisService(llm_client=llm_client, max_themes=settings.max_themes)

    with Session(engine) as session:
        dataset_service = DatasetService(session=session, analysis_service=analysis_service)
        dataset = dataset_service.create_dataset(
            DatasetCreate(name=file_path.stem.replace(\"_\", \" \").title(), source=\"import\")
        )
        payload = file_path.read_bytes()
        dataset_service.ingest_reviews(dataset_id=dataset.id, file_payload=payload, filename=file_path.name)
        print(f\"Ingested sample dataset '{dataset.name}' ({dataset.total_reviews} reviews)\")


if __name__ == \"__main__\":
    parser = argparse.ArgumentParser(description=\"Ingest sample review data into SQLite\")
    parser.add_argument(
        \"path\",
        nargs=\"?\",
        default=\"data/samples/sample_reviews.csv\",
        help=\"Path to CSV or JSON file containing reviews\",
    )
    args = parser.parse_args()
    main(args.path)

