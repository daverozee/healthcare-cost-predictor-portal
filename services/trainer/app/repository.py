from datetime import datetime, timezone
import os
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DatasetVersionRecord, ModelArtifactRecord, TrainingRunRecord
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
        record.error = None
        session.commit()
        session.refresh(record)

        try:
            from app.training.provider_payment import (
                has_provider_payment_target,
                train_provider_payment_model,
                training_settings_from_env,
            )

            dataset_records = [
                session.get(DatasetVersionRecord, dataset_id)
                for dataset_id in record.dataset_version_ids
            ]
            dataset_records = [dataset for dataset in dataset_records if dataset is not None]
            candidates = [
                dataset
                for dataset in dataset_records
                if dataset.raw_uri and dataset.status in {"downloaded", "trainable"}
            ]
            candidates.sort(
                key=lambda dataset: (
                    (dataset.metadata_json or {}).get("grain") != "provider",
                    dataset.created_at,
                )
            )

            selected_dataset = None
            for dataset in candidates:
                if has_provider_payment_target(dataset.raw_uri):
                    selected_dataset = dataset
                    break
            if selected_dataset is None:
                raise ValueError(
                    "No downloaded/trainable dataset version contains Tot_Mdcr_Pymt_Amt."
                )

            artifact_id = f"model_{uuid4().hex[:12]}"
            artifact_dir = Path(os.getenv("MODEL_STORAGE_DIR", "models")) / run_id
            result = train_provider_payment_model(
                csv_path=selected_dataset.raw_uri,
                output_dir=artifact_dir,
                **training_settings_from_env(),
            )
            metrics = {
                **result["metrics"],
                "selected_dataset_version_id": selected_dataset.id,
                "selected_dataset_raw_uri": selected_dataset.raw_uri,
            }

            artifact = ModelArtifactRecord(
                id=artifact_id,
                training_run_id=run_id,
                target=record.target,
                procedure_group=record.procedure_group,
                model_uri=result["model_uri"],
                preprocessor_uri=result["preprocessor_uri"],
                metrics_uri=result["metrics_uri"],
                created_at=datetime.now(timezone.utc),
            )
            record.metrics = metrics
            record.artifact_id = artifact.id
            record.status = TrainingRunStatus.SUCCEEDED.value
            record.finished_at = datetime.now(timezone.utc)
            session.add(artifact)
            session.commit()
            session.refresh(record)
            return run_from_record(record)
        except Exception as exc:
            record.status = TrainingRunStatus.FAILED.value
            record.finished_at = datetime.now(timezone.utc)
            record.error = str(exc)
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
