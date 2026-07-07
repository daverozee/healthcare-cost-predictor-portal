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


def test_registerable_source_can_include_download_homepage():
    source = DEFAULT_SOURCES[-1]

    assert source.homepage_url is not None
    assert source.source_type == "hospital_price_transparency"
