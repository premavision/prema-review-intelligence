from collections.abc import Generator

from fastapi import Depends
from sqlmodel import Session

from app.analysis.llm.client import create_llm_client
from app.analysis.service import ReviewAnalysisService
from app.core.config import settings
from app.db.base import get_session
from app.services.dataset_service import DatasetService

_llm_client = create_llm_client(settings)
_analysis_service = ReviewAnalysisService(llm_client=_llm_client, max_themes=settings.max_themes)


def get_db_session() -> Generator[Session, None, None]:
    yield from get_session()


def get_analysis_service() -> ReviewAnalysisService:
    return _analysis_service


def get_dataset_service(
    session: Session = Depends(get_db_session),
    analysis_service: ReviewAnalysisService = Depends(get_analysis_service),
) -> DatasetService:
    return DatasetService(session=session, analysis_service=analysis_service)

