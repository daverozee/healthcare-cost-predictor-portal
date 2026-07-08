from datetime import datetime, timezone

from app.models import ModelArtifactRecord, TrainingRunRecord
from app.repository import artifact_from_record, resolve_raw_uri, run_from_record


def test_training_run_record_round_trip():
    now = datetime.now(timezone.utc)
    record = TrainingRunRecord(
        id="run_test",
        target="log_allowed_amount",
        procedure_group="mri",
        status="queued",
        dataset_version_ids=["ds_test"],
        model_family="pytorch",
        metrics={},
        created_at=now,
    )

    run = run_from_record(record)

    assert run.id == "run_test"
    assert run.dataset_version_ids == ["ds_test"]
    assert run.status == "queued"


def test_model_artifact_record_round_trip():
    now = datetime.now(timezone.utc)
    record = ModelArtifactRecord(
        id="model_test",
        training_run_id="run_test",
        target="log_allowed_amount",
        procedure_group="mri",
        model_uri="models/run_test/model.pt",
        preprocessor_uri="models/run_test/preprocessor.joblib",
        metrics_uri="models/run_test/metrics.json",
        is_active=True,
        created_at=now,
    )

    artifact = artifact_from_record(record)

    assert artifact.id == "model_test"
    assert artifact.is_active is True
    assert artifact.model_uri.endswith("model.pt")


def test_resolve_raw_uri_returns_existing_path(tmp_path):
    raw = tmp_path / "dataset.csv"
    raw.write_text("a,b\n1,2\n", encoding="utf-8")

    assert resolve_raw_uri(str(raw)) == str(raw)
