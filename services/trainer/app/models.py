from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DataSourceRecord(Base):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[str] = mapped_column(String(120), nullable=False)
    homepage_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class DatasetVersionRecord(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("data_sources.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False, default="0.1")
    raw_uri: Mapped[str | None] = mapped_column(Text)
    normalized_uri: Mapped[str | None] = mapped_column(Text)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    row_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class TrainingRunRecord(Base):
    __tablename__ = "training_runs"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    target: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    procedure_group: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    dataset_version_ids: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    model_family: Mapped[str] = mapped_column(String(80), nullable=False, default="pytorch")
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    artifact_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class ModelArtifactRecord(Base):
    __tablename__ = "model_artifacts"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    training_run_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    procedure_group: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    model_uri: Mapped[str] = mapped_column(Text, nullable=False)
    preprocessor_uri: Mapped[str | None] = mapped_column(Text)
    metrics_uri: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
