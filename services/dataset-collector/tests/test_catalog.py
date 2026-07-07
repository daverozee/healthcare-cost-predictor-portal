from app.catalog import DatasetCatalog


def test_register_dataset_version():
    catalog = DatasetCatalog()
    catalog.seed_defaults()

    version = catalog.register_version(
        source_id="cms-provider-utilization",
        name="CMS provider 2024 sample",
        raw_uri="data/raw/provider-2024.csv",
        row_count=100,
    )

    assert version.id.startswith("ds_")
    assert version.source_id == "cms-provider-utilization"
    assert catalog.list_versions()[0].id == version.id


def test_mark_trainable():
    catalog = DatasetCatalog()
    catalog.seed_defaults()
    version = catalog.register_version(source_id="cms-hospital-outpatient", name="outpatient 2024")

    updated = catalog.mark_trainable(version.id)

    assert updated.status == "trainable"

