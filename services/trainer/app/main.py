from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.registry import registry
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


@app.get("/health")
def health():
    return {"status": "ok", "service": "trainer"}


@app.post("/training-runs", response_model=TrainingRun)
def queue_training_run(request: QueueTrainingRunRequest):
    return registry.queue_run(**request.model_dump())


@app.get("/training-runs", response_model=list[TrainingRun])
def training_runs():
    return registry.list_runs()


@app.get("/training-runs/{run_id}", response_model=TrainingRun)
def training_run(run_id: str):
    try:
        return registry.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/training-runs/{run_id}/run-now", response_model=TrainingRun)
def run_training_now(run_id: str):
    try:
        return registry.run_training_now(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/model-artifacts", response_model=list[ModelArtifact])
def model_artifacts():
    return registry.list_artifacts()


@app.post("/model-artifacts/{artifact_id}/promote", response_model=ModelArtifact)
def promote_artifact(artifact_id: str):
    try:
        return registry.promote_artifact(artifact_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

