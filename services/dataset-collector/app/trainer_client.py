import json
import os
from urllib.request import Request, urlopen


DEFAULT_TRAINER_URL = os.getenv("TRAINER_URL", "http://127.0.0.1:8020")
DEFAULT_TRAINER_TIMEOUT_SECONDS = int(os.getenv("TRAINER_TIMEOUT_SECONDS", "3600"))


class TrainerClient:
    def __init__(self, base_url: str = DEFAULT_TRAINER_URL, timeout_seconds: int = DEFAULT_TRAINER_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _post(self, path: str, payload: dict | None = None) -> dict:
        data = b"{}" if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def queue_training_run(
        self,
        target: str,
        procedure_group: str,
        dataset_version_ids: list[str],
        model_family: str = "pytorch",
    ) -> dict:
        return self._post(
            "/training-runs",
            {
                "target": target,
                "procedure_group": procedure_group,
                "dataset_version_ids": dataset_version_ids,
                "model_family": model_family,
            },
        )

    def run_training_now(self, run_id: str) -> dict:
        return self._post(f"/training-runs/{run_id}/run-now")


trainer_client = TrainerClient()
