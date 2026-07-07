from app.registry import TrainingRegistry


def test_training_run_lifecycle():
    registry = TrainingRegistry()
    run = registry.queue_run(
        target="log_allowed_amount",
        procedure_group="mri",
        dataset_version_ids=["ds_123"],
    )

    assert run.status == "queued"

    finished = registry.run_training_now(run.id)

    assert finished.status == "succeeded"
    assert finished.artifact_id is not None
    assert len(registry.list_artifacts()) == 1


def test_promote_artifact():
    registry = TrainingRegistry()
    run = registry.queue_run(
        target="log_allowed_amount",
        procedure_group="mri",
        dataset_version_ids=["ds_123"],
    )
    finished = registry.run_training_now(run.id)

    promoted = registry.promote_artifact(finished.artifact_id)

    assert promoted.is_active is True

