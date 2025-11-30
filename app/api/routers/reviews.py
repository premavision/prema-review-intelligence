from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_dataset_service
from app.schemas.reviews import ReviewRead
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewRead])
def list_reviews(
    dataset_id: int | None = Query(default=None),
    min_rating: int | None = Query(default=None, ge=1, le=5),
    max_rating: int | None = Query(default=None, ge=1, le=5),
    limit: int = Query(default=100, ge=1, le=500),
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> list[ReviewRead]:
    reviews = dataset_service.list_reviews(
        dataset_id=dataset_id,
        min_rating=min_rating,
        max_rating=max_rating,
        limit=limit,
    )
    return [
        ReviewRead.model_validate(review.model_dump(exclude={"dataset"}))
        for review in reviews
    ]

