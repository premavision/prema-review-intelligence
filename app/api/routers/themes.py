from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_dataset_service
from app.schemas.analysis import Theme
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets/{dataset_id}/themes", tags=["themes"])


@router.get("", response_model=list[Theme])
def list_themes(
    dataset_id: int,
    dataset_service: DatasetService = Depends(get_dataset_service),  # noqa: B008
) -> list[Theme]:
    analysis = dataset_service.get_dataset_analysis(dataset_id, force_refresh=False)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis available for dataset",
        )
    return analysis.themes
