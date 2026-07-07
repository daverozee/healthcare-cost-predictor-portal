from app.repository import DEFAULT_SOURCES, source_from_record, source_to_record


def test_default_sources_include_cms_and_transparency():
    source_ids = {source.id for source in DEFAULT_SOURCES}

    assert "cms-provider-utilization" in source_ids
    assert "cms-hospital-outpatient" in source_ids
    assert "hospital-price-transparency" in source_ids


def test_data_source_record_round_trip():
    source = DEFAULT_SOURCES[0]
    record = source_to_record(source)
    restored = source_from_record(record)

    assert restored == source

