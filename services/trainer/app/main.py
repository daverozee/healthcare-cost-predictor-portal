from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_session, init_database
from app.repository import repository
from healthcost_shared import ModelArtifact, TrainingRun


class QueueTrainingRunRequest(BaseModel):
    target: str = Field(examples=["log_allowed_amount"])
    procedure_group: str = Field(examples=["mri"])
    dataset_version_ids: list[str]
    model_family: str = "pytorch"


app = FastAPI(
    title="Trainer Service",
    version="0.1.0",
    description="Queues and tracks PyTorch training runs for healthcare cost models.",
)


@app.on_event("startup")
def startup() -> None:
    init_database()


@app.get("/health")
def health():
    return {"status": "ok", "service": "trainer"}


@app.post("/training-runs", response_model=TrainingRun)
def queue_training_run(request: QueueTrainingRunRequest, session: Session = Depends(get_session)):
    return repository.queue_run(session, **request.model_dump())


@app.get("/training-runs", response_model=list[TrainingRun])
def training_runs(session: Session = Depends(get_session)):
    return repository.list_runs(session)


@app.get("/training-runs/{run_id}", response_model=TrainingRun)
def training_run(run_id: str, session: Session = Depends(get_session)):
    try:
        return repository.get_run(session, run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/training-runs/{run_id}/run-now", response_model=TrainingRun)
def run_training_now(run_id: str, session: Session = Depends(get_session)):
    try:
        return repository.run_training_now(session, run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/model-artifacts", response_model=list[ModelArtifact])
def model_artifacts(session: Session = Depends(get_session)):
    return repository.list_artifacts(session)


@app.post("/model-artifacts/{artifact_id}/promote", response_model=ModelArtifact)
def promote_artifact(artifact_id: str, session: Session = Depends(get_session)):
    try:
        return repository.promote_artifact(session, artifact_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
