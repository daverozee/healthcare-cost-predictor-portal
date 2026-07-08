import pytest

import app.storage as storage
from app.storage import checksum_file, download_url, safe_filename


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


class FakeDownloadResponse:
    headers = {"Content-Length": "10"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size):
        return b"0123456789"


def test_download_url_rejects_oversized_content_length(monkeypatch, tmp_path):
    def fake_urlopen(request, timeout):
        return FakeDownloadResponse()

    monkeypatch.setattr(storage, "urlopen", fake_urlopen)

    with pytest.raises(ValueError):
        download_url("https://example.com/file.csv", "ds_test", storage_dir=tmp_path, max_bytes=5)

    assert list(tmp_path.glob("*.part")) == []
