from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.catalog import catalog
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


@app.get("/health")
def health():
    return {"status": "ok", "service": "dataset-collector"}


@app.get("/sources", response_model=list[DataSource])
def sources():
    return catalog.list_sources()


@app.post("/dataset-versions", response_model=DatasetVersion)
def register_dataset_version(request: RegisterDatasetVersionRequest):
    try:
        return catalog.register_version(**request.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/dataset-versions", response_model=list[DatasetVersion])
def dataset_versions(status: DatasetStatus | None = Query(default=None)):
    return catalog.list_versions(status=status)


@app.post("/dataset-versions/{dataset_version_id}/mark-trainable", response_model=DatasetVersion)
def mark_trainable(dataset_version_id: str):
    try:
        return catalog.mark_trainable(dataset_version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

