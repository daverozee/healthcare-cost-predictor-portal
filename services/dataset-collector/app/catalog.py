from datetime import datetime, timezone
from uuid import uuid4

from healthcost_shared import DataSource, DatasetStatus, DatasetVersion


class DatasetCatalog:
    def __init__(self):
        self.sources: dict[str, DataSource] = {}
        self.versions: dict[str, DatasetVersion] = {}

    def seed_defaults(self) -> None:
        self.register_source(
            DataSource(
                id="cms-provider-utilization",
                name="CMS Medicare Physician & Other Practitioners",
                source_type="cms",
                homepage_url="https://data.cms.gov/",
                notes="Provider-level utilization and payment public use files.",
            )
        )
        self.register_source(
            DataSource(
                id="cms-hospital-outpatient",
                name="CMS Hospital Outpatient Public Use Files",
                source_type="cms",
                homepage_url="https://data.cms.gov/",
                notes="Hospital outpatient charges and Medicare payment data.",
            )
        )
        self.register_source(
            DataSource(
                id="hospital-price-transparency",
                name="Hospital Price Transparency Machine-Readable Files",
                source_type="hospital_price_transparency",
                homepage_url="https://www.cms.gov/priorities/key-initiatives/hospital-price-transparency",
                notes="Hospital standard charges and payer-specific negotiated rates.",
            )
        )

    def register_source(self, source: DataSource) -> DataSource:
        self.sources[source.id] = source
        return source

    def list_sources(self) -> list[DataSource]:
        return sorted(self.sources.values(), key=lambda source: source.id)

    def register_version(
        self,
        source_id: str,
        name: str,
        raw_uri: str | None = None,
        normalized_uri: str | None = None,
        checksum_sha256: str | None = None,
        row_count: int | None = None,
    ) -> DatasetVersion:
        if source_id not in self.sources:
            raise KeyError(f"Unknown source_id: {source_id}")

        dataset_version = DatasetVersion(
            id=f"ds_{uuid4().hex[:12]}",
            source_id=source_id,
            name=name,
            status=DatasetStatus.REGISTERED,
            raw_uri=raw_uri,
            normalized_uri=normalized_uri,
            checksum_sha256=checksum_sha256,
            row_count=row_count,
            created_at=datetime.now(timezone.utc),
        )
        self.versions[dataset_version.id] = dataset_version
        return dataset_version

    def list_versions(self, status: DatasetStatus | None = None) -> list[DatasetVersion]:
        versions = list(self.versions.values())
        if status is not None:
            versions = [version for version in versions if version.status == status]
        return sorted(versions, key=lambda version: version.created_at, reverse=True)

    def mark_trainable(self, dataset_version_id: str) -> DatasetVersion:
        if dataset_version_id not in self.versions:
            raise KeyError(f"Unknown dataset_version_id: {dataset_version_id}")
        version = self.versions[dataset_version_id].model_copy(update={"status": DatasetStatus.TRAINABLE})
        self.versions[dataset_version_id] = version
        return version


catalog = DatasetCatalog()
catalog.seed_defaults()

