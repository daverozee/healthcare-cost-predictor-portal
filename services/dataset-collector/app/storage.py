import hashlib
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


DEFAULT_STORAGE_DIR = Path(os.getenv("COLLECTOR_STORAGE_DIR", "data/raw"))
CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class StoredDownload:
    uri: str
    checksum_sha256: str
    byte_count: int
    downloaded_at: datetime


def safe_filename(url: str, fallback: str) -> str:
    parsed = urlparse(url)
    candidate = unquote(Path(parsed.path).name) if parsed.path else ""
    if not candidate:
        candidate = fallback
    candidate = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate).strip(".-")
    return candidate or fallback


def checksum_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_SIZE), b""):
            digest.update(chunk)
            byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def download_url(
    url: str,
    dataset_version_id: str,
    storage_dir: Path = DEFAULT_STORAGE_DIR,
    filename: str | None = None,
    max_bytes: int | None = None,
) -> StoredDownload:
    storage_dir.mkdir(parents=True, exist_ok=True)
    destination_name = filename or safe_filename(url, f"{dataset_version_id}.bin")
    destination = storage_dir / f"{dataset_version_id}-{destination_name}"
    temporary = destination.with_suffix(destination.suffix + ".part")

    try:
        request = Request(url, headers={"User-Agent": "healthcare-cost-predictor-collector/0.1"})
        with urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            content_length = response.headers.get("Content-Length")
            if max_bytes is not None and content_length and int(content_length) > max_bytes:
                raise ValueError(f"Download is larger than max_bytes: {content_length} > {max_bytes}")

            byte_count = 0
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                byte_count += len(chunk)
                if max_bytes is not None and byte_count > max_bytes:
                    raise ValueError(f"Download exceeded max_bytes: {byte_count} > {max_bytes}")
                output.write(chunk)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    checksum_sha256, byte_count = checksum_file(temporary)
    temporary.replace(destination)

    return StoredDownload(
        uri=str(destination),
        checksum_sha256=checksum_sha256,
        byte_count=byte_count,
        downloaded_at=datetime.now(timezone.utc),
    )
