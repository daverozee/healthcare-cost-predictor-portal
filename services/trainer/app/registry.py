from datetime import datetime, timezone
from uuid import uuid4

from healthcost_shared import ModelArtifact, TrainingRun, TrainingRunStatus


class TrainingRegistry:
    def __init__(self):
        self.runs: dict[str, TrainingRun] = {}
        self.artifacts: dict[str, ModelArtifact] = {}

    def queue_run(
        self,
        target: str,
        procedure_group: str,
        dataset_version_ids: list[str],
        model_family: str = "pytorch",
    ) -> TrainingRun:
        run = TrainingRun(
            id=f"run_{uuid4().hex[:12]}",
            target=target,
            procedure_group=procedure_group,
            status=TrainingRunStatus.QUEUED,
            dataset_version_ids=dataset_version_ids,
            model_family=model_family,
            created_at=datetime.now(timezone.utc),
        )
        self.runs[run.id] = run
        return run

    def list_runs(self) -> list[TrainingRun]:
        return sorted(self.runs.values(), key=lambda run: run.created_at, reverse=True)

    def get_run(self, run_id: str) -> TrainingRun:
        if run_id not in self.runs:
            raise KeyError(f"Unknown run_id: {run_id}")
        return self.runs[run_id]

    def run_training_now(self, run_id: str) -> TrainingRun:
        run = self.get_run(run_id)
        started = datetime.now(timezone.utc)
        running = run.model_copy(update={"status": TrainingRunStatus.RUNNING, "started_at": started})
        self.runs[run_id] = running

        artifact = ModelArtifact(
            id=f"model_{uuid4().hex[:12]}",
            training_run_id=run_id,
            target=run.target,
            procedure_group=run.procedure_group,
            model_uri=f"models/{run_id}/model.pt",
            preprocessor_uri=f"models/{run_id}/preprocessor.joblib",
            metrics_uri=f"models/{run_id}/metrics.json",
            created_at=datetime.now(timezone.utc),
        )
        metrics = {
            "mae_log": 0.0,
            "rmse_log": 0.0,
            "r2_log": 0.0,
        }
        finished = datetime.now(timezone.utc)
        succeeded = running.model_copy(
            update={
                "status": TrainingRunStatus.SUCCEEDED,
                "finished_at": finished,
                "metrics": metrics,
                "artifact_id": artifact.id,
            }
        )
        self.artifacts[artifact.id] = artifact
        self.runs[run_id] = succeeded
        return succeeded

    def list_artifacts(self) -> list[ModelArtifact]:
        return sorted(self.artifacts.values(), key=lambda artifact: artifact.created_at, reverse=True)

    def promote_artifact(self, artifact_id: str) -> ModelArtifact:
        if artifact_id not in self.artifacts:
            raise KeyError(f"Unknown artifact_id: {artifact_id}")

        artifact = self.artifacts[artifact_id]
        for existing_id, existing in list(self.artifacts.items()):
            if existing.target == artifact.target and existing.procedure_group == artifact.procedure_group:
                self.artifacts[existing_id] = existing.model_copy(update={"is_active": False})

        promoted = artifact.model_copy(update={"is_active": True})
        self.artifacts[artifact_id] = promoted
        return promoted


registry = TrainingRegistry()

