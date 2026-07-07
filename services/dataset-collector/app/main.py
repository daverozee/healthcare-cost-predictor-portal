from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session, get_session_factory, init_database
from app.repository import repository
from healthcost_shared import DataSource, DatasetStatus, DatasetVersion


class RegisterDatasetVersionRequest(BaseModel):
    source_id: str
    name: str
    raw_uri: str | None = None
    normalized_uri: str | None = None
    checksum_sha256: str | None = None
    row_count: int | None = None


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


@app.post("/dataset-versions/{dataset_version_id}/mark-trainable", response_model=DatasetVersion)
def mark_trainable(dataset_version_id: str, session: Session = Depends(get_session)):
    try:
        return repository.mark_trainable(session, dataset_version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
