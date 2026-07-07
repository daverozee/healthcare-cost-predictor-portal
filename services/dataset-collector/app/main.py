from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agent import collection_agent
from app.db import get_session, get_session_factory, init_database
from app.repository import repository
from app.storage import download_url
from healthcost_shared import AgentRun, DataSource, DatasetStatus, DatasetVersion


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


class AgentRunRequest(BaseModel):
    goal: str = Field(
        default="cms_starter",
        description="Collection goal. Current deterministic goals: cms_starter, starter, provider_cost_starter.",
    )
    limit: int = Field(default=5, ge=1, le=20)


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


@app.post("/agent-runs", response_model=AgentRun)
def create_agent_run(request: AgentRunRequest, session: Session = Depends(get_session)):
    policy, proposals = collection_agent.propose(request.goal, limit=request.limit)
    if not proposals:
        raise HTTPException(status_code=404, detail=f"No proposals available for goal: {request.goal}")
    return repository.create_agent_run(
        session,
        goal=request.goal,
        policy=policy,
        proposals=proposals,
    )


@app.get("/agent-runs", response_model=list[AgentRun])
def agent_runs(session: Session = Depends(get_session)):
    return repository.list_agent_runs(session)


@app.get("/agent-runs/{agent_run_id}", response_model=AgentRun)
def agent_run(agent_run_id: str, session: Session = Depends(get_session)):
    try:
        return repository.get_agent_run(session, agent_run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/agent-runs/{agent_run_id}/apply", response_model=AgentRun)
def apply_agent_run(agent_run_id: str, session: Session = Depends(get_session)):
    try:
        run = repository.get_agent_run(session, agent_run_id)
        created_ids = []
        for proposal in run.proposals:
            dataset = repository.register_version(
                session,
                source_id=proposal["source_id"],
                name=proposal["name"],
                source_url=proposal["source_url"],
                metadata={
                    **proposal.get("metadata", {}),
                    "agent_run_id": agent_run_id,
                    "agent_rationale": proposal.get("rationale"),
                    "requires_human_review_before_download": True,
                },
            )
            created_ids.append(dataset.id)
        return repository.mark_agent_run_applied(session, agent_run_id, created_ids)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
