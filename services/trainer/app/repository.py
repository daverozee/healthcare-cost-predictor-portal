from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ModelArtifactRecord, TrainingRunRecord
from healthcost_shared import ModelArtifact, TrainingRun, TrainingRunStatus


def run_from_record(record: TrainingRunRecord) -> TrainingRun:
    return TrainingRun(
        id=record.id,
        target=record.target,
        procedure_group=record.procedure_group,
        status=TrainingRunStatus(record.status),
        dataset_version_ids=record.dataset_version_ids,
        model_family=record.model_family,
        metrics=record.metrics or {},
        artifact_id=record.artifact_id,
        created_at=record.created_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
        error=record.error,
    )


def artifact_from_record(record: ModelArtifactRecord) -> ModelArtifact:
    return ModelArtifact(
        id=record.id,
        training_run_id=record.training_run_id,
        target=record.target,
        procedure_group=record.procedure_group,
        model_uri=record.model_uri,
        preprocessor_uri=record.preprocessor_uri,
        metrics_uri=record.metrics_uri,
        is_active=record.is_active,
        created_at=record.created_at,
    )


class TrainingRepository:
    def queue_run(
        self,
        session: Session,
        target: str,
        procedure_group: str,
        dataset_version_ids: list[str],
        model_family: str = "pytorch",
    ) -> TrainingRun:
        record = TrainingRunRecord(
            id=f"run_{uuid4().hex[:12]}",
            target=target,
            procedure_group=procedure_group,
            status=TrainingRunStatus.QUEUED.value,
            dataset_version_ids=dataset_version_ids,
            model_family=model_family,
            metrics={},
            created_at=datetime.now(timezone.utc),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return run_from_record(record)

    def list_runs(self, session: Session) -> list[TrainingRun]:
        statement = select(TrainingRunRecord).order_by(TrainingRunRecord.created_at.desc())
        return [run_from_record(record) for record in session.scalars(statement).all()]

    def get_run(self, session: Session, run_id: str) -> TrainingRun:
        record = session.get(TrainingRunRecord, run_id)
        if record is None:
            raise KeyError(f"Unknown run_id: {run_id}")
        return run_from_record(record)

    def run_training_now(self, session: Session, run_id: str) -> TrainingRun:
        record = session.get(TrainingRunRecord, run_id)
        if record is None:
            raise KeyError(f"Unknown run_id: {run_id}")

        record.status = TrainingRunStatus.RUNNING.value
        record.started_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(record)

        artifact = ModelArtifactRecord(
            id=f"model_{uuid4().hex[:12]}",
            training_run_id=run_id,
            target=record.target,
            procedure_group=record.procedure_group,
            model_uri=f"models/{run_id}/model.pt",
            preprocessor_uri=f"models/{run_id}/preprocessor.joblib",
            metrics_uri=f"models/{run_id}/metrics.json",
            created_at=datetime.now(timezone.utc),
        )
        record.metrics = {
            "mae_log": 0.0,
            "rmse_log": 0.0,
            "r2_log": 0.0,
        }
        record.artifact_id = artifact.id
        record.status = TrainingRunStatus.SUCCEEDED.value
        record.finished_at = datetime.now(timezone.utc)
        session.add(artifact)
        session.commit()
        session.refresh(record)
        return run_from_record(record)

    def list_artifacts(self, session: Session) -> list[ModelArtifact]:
        statement = select(ModelArtifactRecord).order_by(ModelArtifactRecord.created_at.desc())
        return [artifact_from_record(record) for record in session.scalars(statement).all()]

    def promote_artifact(self, session: Session, artifact_id: str) -> ModelArtifact:
        artifact = session.get(ModelArtifactRecord, artifact_id)
        if artifact is None:
            raise KeyError(f"Unknown artifact_id: {artifact_id}")

        statement = select(ModelArtifactRecord).where(
            ModelArtifactRecord.target == artifact.target,
            ModelArtifactRecord.procedure_group == artifact.procedure_group,
        )
        for record in session.scalars(statement):
            record.is_active = False

        artifact.is_active = True
        session.commit()
        session.refresh(artifact)
        return artifact_from_record(artifact)


repository = TrainingRepository()

