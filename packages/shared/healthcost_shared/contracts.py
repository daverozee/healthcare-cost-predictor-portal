from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class DatasetStatus(StrEnum):
    REGISTERED = "registered"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    TRAINABLE = "trainable"
    ARCHIVED = "archived"


class TrainingRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PROMOTED = "promoted"


class AgentRunStatus(StrEnum):
    PROPOSED = "proposed"
    APPLIED = "applied"
    FAILED = "failed"


class DataSource(BaseModel):
    id: str
    name: str
    source_type: str = Field(examples=["cms", "hospital_price_transparency"])
    homepage_url: str | None = None
    notes: str | None = None


class DatasetVersion(BaseModel):
    id: str
    source_id: str
    name: str
    status: DatasetStatus
    schema_version: str = "0.1"
    raw_uri: str | None = None
    normalized_uri: str | None = None
    checksum_sha256: str | None = None
    row_count: int | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class TrainingRun(BaseModel):
    id: str
    target: str
    procedure_group: str
    status: TrainingRunStatus
    dataset_version_ids: list[str]
    model_family: str = "pytorch"
    metrics: dict[str, float] = Field(default_factory=dict)
    artifact_id: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class ModelArtifact(BaseModel):
    id: str
    training_run_id: str
    target: str
    procedure_group: str
    model_uri: str
    preprocessor_uri: str | None = None
    metrics_uri: str | None = None
    is_active: bool = False
    created_at: datetime


class AgentRun(BaseModel):
    id: str
    goal: str
    status: AgentRunStatus
    policy: dict[str, Any] = Field(default_factory=dict)
    proposals: list[dict[str, Any]] = Field(default_factory=list)
    created_dataset_version_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    applied_at: datetime | None = None
    error: str | None = None
