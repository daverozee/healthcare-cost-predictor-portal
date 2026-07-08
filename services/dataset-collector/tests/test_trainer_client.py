import json

import app.trainer_client as trainer_client_module
from app.trainer_client import TrainerClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_queue_training_run_posts_expected_payload(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"id": "run_test", "status": "queued"})

    monkeypatch.setattr(trainer_client_module, "urlopen", fake_urlopen)

    client = TrainerClient("http://trainer:8020")
    response = client.queue_training_run(
        target="log_allowed_amount",
        procedure_group="cms_starter",
        dataset_version_ids=["ds_test"],
    )

    assert response["id"] == "run_test"
    assert captured["url"] == "http://trainer:8020/training-runs"
    assert captured["payload"]["dataset_version_ids"] == ["ds_test"]

