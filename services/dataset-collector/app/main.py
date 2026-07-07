from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_session, get_session_factory, init_database
from app.repository import repository
from app.storage import download_url
from healthcost_shared import DataSource, DatasetStatus, DatasetVersion


class RegisterDatasetVersionRequest(BaseModel):
    source_id: str
    name: str
    raw_uri: str | None = None
    normalized_uri: str | None = None
    checksum_sha256: str | None = None
    row_count: int | None = None
    source_url: str | None = Field(
        default=None,
        description="Original public URL to download later.",
    )
    metadata: dict = Field(default_factory=dict)


class DownloadDatasetVersionRequest(BaseModel):
    url: str | None = Field(
        default=None,
        description="Override download URL. If omitted, uses metadata.source_url.",
    )
    filename: str | None = Field(default=None, description="Optional stored filename.")


app = FastAPI(
    title="Dataset Collector Service",
    version="0.1.0",
    description="Tracks public healthcare dataset sources and dataset versions.",
)


@app.on_event("startup")
def startup() -> None:
    init_database()
    with get_session_factory()() as session:
        repository.seed_defaults(session)


@app.get("/health")
def health():
    return {"status": "ok", "service": "dataset-collector"}


@app.get("/sources", response_model=list[DataSource])
def sources(session: Session = Depends(get_session)):
    return repository.list_sources(session)


@app.post("/sources", response_model=DataSource)
def register_source(source: DataSource, session: Session = Depends(get_session)):
    return repository.register_source(session, source)


@app.post("/dataset-versions", response_model=DatasetVersion)
def register_dataset_version(
    request: RegisterDatasetVersionRequest,
    session: Session = Depends(get_session),
):
    try:
        return repository.register_version(session, **request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/dataset-versions", response_model=list[DatasetVersion])
def dataset_versions(
    status: DatasetStatus | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return repository.list_versions(session, status=status)


@app.get("/dataset-versions/{dataset_version_id}", response_model=DatasetVersion)
def dataset_version(dataset_version_id: str, session: Session = Depends(get_session)):
    try:
        return repository.get_version(session, dataset_version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/dataset-versions/{dataset_version_id}/download", response_model=DatasetVersion)
def download_dataset_version(
    dataset_version_id: str,
    request: DownloadDatasetVersionRequest,
    session: Session = Depends(get_session),
):
    try:
        dataset = repository.get_version(session, dataset_version_id)
        source_url = request.url or dataset.metadata.get("source_url")
        if not source_url:
            raise HTTPException(
                status_code=400,
                detail="No download URL supplied. Pass request.url or register metadata.source_url.",
            )

        repository.update_status(
            session,
            dataset_version_id,
            DatasetStatus.DOWNLOADING,
            {"download_started_at": datetime.now(timezone.utc).isoformat()},
        )
        stored = download_url(source_url, dataset_version_id, filename=request.filename)
        return repository.record_download(
            session,
            dataset_version_id=dataset_version_id,
            raw_uri=stored.uri,
            checksum_sha256=stored.checksum_sha256,
            byte_count=stored.byte_count,
            source_url=source_url,
            downloaded_at=stored.downloaded_at,
        )
    except HTTPException:
        raise
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        repository.update_status(
            session,
            dataset_version_id,
            DatasetStatus.FAILED,
            {"download_error": str(exc)},
        )
        raise HTTPException(status_code=502, detail=f"Download failed: {exc}") from exc


@app.post("/dataset-versions/{dataset_version_id}/mark-trainable", response_model=DatasetVersion)
def mark_trainable(dataset_version_id: str, session: Session = Depends(get_session)):
    try:
        return repository.mark_trainable(session, dataset_version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
