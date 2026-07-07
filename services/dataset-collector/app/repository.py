from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentRunRecord, DataSourceRecord, DatasetVersionRecord
from healthcost_shared import AgentRun, AgentRunStatus, DataSource, DatasetStatus, DatasetVersion


DEFAULT_SOURCES = [
    DataSource(
        id="cms-provider-utilization",
        name="CMS Medicare Physician & Other Practitioners",
        source_type="cms",
        homepage_url="https://data.cms.gov/",
        notes="Provider-level utilization and payment public use files.",
    ),
    DataSource(
        id="cms-hospital-outpatient",
        name="CMS Hospital Outpatient Public Use Files",
        source_type="cms",
        homepage_url="https://data.cms.gov/",
        notes="Hospital outpatient charges and Medicare payment data.",
    ),
    DataSource(
        id="hospital-price-transparency",
        name="Hospital Price Transparency Machine-Readable Files",
        source_type="hospital_price_transparency",
        homepage_url="https://www.cms.gov/priorities/key-initiatives/hospital-price-transparency",
        notes="Hospital standard charges and payer-specific negotiated rates.",
    ),
]


def source_to_record(source: DataSource) -> DataSourceRecord:
    return DataSourceRecord(**source.model_dump())


def source_from_record(record: DataSourceRecord) -> DataSource:
    return DataSource(
        id=record.id,
        name=record.name,
        source_type=record.source_type,
        homepage_url=record.homepage_url,
        notes=record.notes,
    )


def version_from_record(record: DatasetVersionRecord) -> DatasetVersion:
    return DatasetVersion(
        id=record.id,
        source_id=record.source_id,
        name=record.name,
        status=DatasetStatus(record.status),
        schema_version=record.schema_version,
        raw_uri=record.raw_uri,
        normalized_uri=record.normalized_uri,
        checksum_sha256=record.checksum_sha256,
        row_count=record.row_count,
        created_at=record.created_at,
        metadata=record.metadata_json or {},
    )


def agent_run_from_record(record: AgentRunRecord) -> AgentRun:
    return AgentRun(
        id=record.id,
        goal=record.goal,
        status=AgentRunStatus(record.status),
        policy=record.policy_json or {},
        proposals=record.proposals_json or [],
        created_dataset_version_ids=record.created_dataset_version_ids or [],
        created_at=record.created_at,
        applied_at=record.applied_at,
        error=record.error,
    )


class DatasetCatalogRepository:
    def seed_defaults(self, session: Session) -> None:
        for source in DEFAULT_SOURCES:
            if session.get(DataSourceRecord, source.id) is None:
                session.add(source_to_record(source))
        session.commit()

    def register_source(self, session: Session, source: DataSource) -> DataSource:
        record = session.get(DataSourceRecord, source.id)
        if record is None:
            record = source_to_record(source)
            session.add(record)
        else:
            record.name = source.name
            record.source_type = source.source_type
            record.homepage_url = source.homepage_url
            record.notes = source.notes
        session.commit()
        session.refresh(record)
        return source_from_record(record)

    def list_sources(self, session: Session) -> list[DataSource]:
        records = session.scalars(select(DataSourceRecord).order_by(DataSourceRecord.id)).all()
        return [source_from_record(record) for record in records]

    def register_version(
        self,
        session: Session,
        source_id: str,
        name: str,
        raw_uri: str | None = None,
        normalized_uri: str | None = None,
        checksum_sha256: str | None = None,
        row_count: int | None = None,
        source_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DatasetVersion:
        if session.get(DataSourceRecord, source_id) is None:
            raise KeyError(f"Unknown source_id: {source_id}")

        metadata_json = dict(metadata or {})
        if source_url:
            metadata_json["source_url"] = source_url

        record = DatasetVersionRecord(
            id=f"ds_{uuid4().hex[:12]}",
            source_id=source_id,
            name=name,
            status=DatasetStatus.REGISTERED.value,
            raw_uri=raw_uri,
            normalized_uri=normalized_uri,
            checksum_sha256=checksum_sha256,
            row_count=row_count,
            created_at=datetime.now(timezone.utc),
            metadata_json=metadata_json,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return version_from_record(record)

    def list_versions(self, session: Session, status: DatasetStatus | None = None) -> list[DatasetVersion]:
        statement = select(DatasetVersionRecord)
        if status is not None:
            statement = statement.where(DatasetVersionRecord.status == status.value)
        statement = statement.order_by(DatasetVersionRecord.created_at.desc())
        records = session.scalars(statement).all()
        return [version_from_record(record) for record in records]

    def get_version(self, session: Session, dataset_version_id: str) -> DatasetVersion:
        record = session.get(DatasetVersionRecord, dataset_version_id)
        if record is None:
            raise KeyError(f"Unknown dataset_version_id: {dataset_version_id}")
        return version_from_record(record)

    def update_status(
        self,
        session: Session,
        dataset_version_id: str,
        status: DatasetStatus,
        metadata_patch: dict[str, Any] | None = None,
    ) -> DatasetVersion:
        record = session.get(DatasetVersionRecord, dataset_version_id)
        if record is None:
            raise KeyError(f"Unknown dataset_version_id: {dataset_version_id}")
        record.status = status.value
        if metadata_patch:
            record.metadata_json = {**(record.metadata_json or {}), **metadata_patch}
        session.commit()
        session.refresh(record)
        return version_from_record(record)

    def record_download(
        self,
        session: Session,
        dataset_version_id: str,
        raw_uri: str,
        checksum_sha256: str,
        byte_count: int,
        source_url: str,
        downloaded_at: datetime,
    ) -> DatasetVersion:
        record = session.get(DatasetVersionRecord, dataset_version_id)
        if record is None:
            raise KeyError(f"Unknown dataset_version_id: {dataset_version_id}")

        record.status = DatasetStatus.DOWNLOADED.value
        record.raw_uri = raw_uri
        record.checksum_sha256 = checksum_sha256
        record.metadata_json = {
            **(record.metadata_json or {}),
            "source_url": source_url,
            "byte_count": byte_count,
            "downloaded_at": downloaded_at.isoformat(),
        }
        session.commit()
        session.refresh(record)
        return version_from_record(record)

    def mark_trainable(self, session: Session, dataset_version_id: str) -> DatasetVersion:
        record = session.get(DatasetVersionRecord, dataset_version_id)
        if record is None:
            raise KeyError(f"Unknown dataset_version_id: {dataset_version_id}")
        record.status = DatasetStatus.TRAINABLE.value
        session.commit()
        session.refresh(record)
        return version_from_record(record)

    def create_agent_run(
        self,
        session: Session,
        goal: str,
        policy: dict[str, Any],
        proposals: list[dict[str, Any]],
    ) -> AgentRun:
        record = AgentRunRecord(
            id=f"agent_{uuid4().hex[:12]}",
            goal=goal,
            status=AgentRunStatus.PROPOSED.value,
            policy_json=policy,
            proposals_json=proposals,
            created_dataset_version_ids=[],
            created_at=datetime.now(timezone.utc),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return agent_run_from_record(record)

    def list_agent_runs(self, session: Session) -> list[AgentRun]:
        records = session.scalars(select(AgentRunRecord).order_by(AgentRunRecord.created_at.desc())).all()
        return [agent_run_from_record(record) for record in records]

    def get_agent_run(self, session: Session, agent_run_id: str) -> AgentRun:
        record = session.get(AgentRunRecord, agent_run_id)
        if record is None:
            raise KeyError(f"Unknown agent_run_id: {agent_run_id}")
        return agent_run_from_record(record)

    def mark_agent_run_applied(
        self,
        session: Session,
        agent_run_id: str,
        created_dataset_version_ids: list[str],
    ) -> AgentRun:
        record = session.get(AgentRunRecord, agent_run_id)
        if record is None:
            raise KeyError(f"Unknown agent_run_id: {agent_run_id}")
        record.status = AgentRunStatus.APPLIED.value
        record.created_dataset_version_ids = created_dataset_version_ids
        record.applied_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(record)
        return agent_run_from_record(record)


repository = DatasetCatalogRepository()
