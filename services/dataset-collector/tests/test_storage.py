from app.storage import checksum_file, safe_filename


def test_safe_filename_uses_url_name():
    filename = safe_filename("https://example.com/path/My File (2024).csv?download=1", "fallback.bin")

    assert filename == "My-File-2024-.csv"


def test_safe_filename_uses_fallback_when_url_has_no_name():
    filename = safe_filename("https://example.com/", "dataset.bin")

    assert filename == "dataset.bin"


def test_checksum_file(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("hello", encoding="utf-8")

    checksum, byte_count = checksum_file(path)

    assert checksum == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert byte_count == 5

