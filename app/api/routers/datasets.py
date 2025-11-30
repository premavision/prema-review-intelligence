from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import get_dataset_service
from app.core.config import settings
from app.schemas.datasets import (
    DatasetCreate,
    DatasetIngestionResponse,
    DatasetListResponse,
    DatasetRead,
    DatasetSummaryResponse,
)
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])

ALLOWED_EXTENSIONS = {".csv", ".json", ".ndjson"}


def validate_file_upload(file: UploadFile | None, max_size: int) -> None:
    """Validate file upload for security."""
    if not file:
        return

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Note: FastAPI's UploadFile doesn't expose size before reading
    # We'll validate size after reading in the ingestion service


@router.post("", response_model=DatasetIngestionResponse)
async def create_dataset(
    name: str = Form(...),
    source: str = Form("import"),
    description: str | None = Form(None),
    file: UploadFile | None = File(None),
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> DatasetIngestionResponse:
    # Validate file upload before processing
    validate_file_upload(file, max_size=settings.max_upload_size)
    
    dataset_payload = DatasetCreate(name=name, source=source, description=description)
    dataset = dataset_service.create_dataset(dataset_payload)
    imported = 0
    warnings: list[str] = []
    if file:
        payload = await file.read()
        
        # Validate file size after reading
        if len(payload) > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.max_upload_size} bytes",
            )
        
        dataset, ingestion_result = dataset_service.ingest_reviews(
            dataset_id=dataset.id,
            file_payload=payload,
            filename=file.filename or "unknown",
        )
        imported = ingestion_result.imported
        warnings = ingestion_result.warnings
    dataset_read = DatasetRead.model_validate(dataset.model_dump(exclude={"reviews", "analysis"}))
    return DatasetIngestionResponse(dataset=dataset_read, imported_reviews=imported, warnings=warnings)


@router.get("", response_model=DatasetListResponse)
def list_datasets(dataset_service: DatasetService = Depends(get_dataset_service)) -> DatasetListResponse:
    datasets = [
        DatasetRead.model_validate(ds.model_dump(exclude={"reviews", "analysis"}))
        for ds in dataset_service.list_datasets()
    ]
    return DatasetListResponse(datasets=datasets)


@router.get("/{dataset_id}/summary", response_model=DatasetSummaryResponse)
def dataset_summary(
    dataset_id: int,
    force: bool = False,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> DatasetSummaryResponse:
    dataset = dataset_service.get_dataset(dataset_id)
    dataset_read = DatasetRead.model_validate(dataset.model_dump(exclude={"reviews", "analysis"}))
    analysis = dataset_service.get_dataset_analysis(dataset_id, force_refresh=force)
    return DatasetSummaryResponse(dataset=dataset_read, analysis=analysis)

