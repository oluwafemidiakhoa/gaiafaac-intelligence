from __future__ import annotations

import contextlib
import tempfile
from collections.abc import Iterator
from pathlib import Path

from gaiafaac_api.config import Settings, get_settings

_SCHEME = "s3://"


def object_storage_configured(settings: Settings) -> bool:
    return bool(
        settings.source_archive_bucket
        and settings.source_archive_endpoint
        and settings.source_archive_access_key_id
        and settings.source_archive_secret_access_key
    )


def _client(settings: Settings):
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.source_archive_endpoint,
        aws_access_key_id=settings.source_archive_access_key_id,
        aws_secret_access_key=settings.source_archive_secret_access_key,
        region_name=settings.source_archive_region or "auto",
    )


def put_source_object(
    *,
    key: str,
    body: bytes,
    content_type: str,
    settings: Settings | None = None,
) -> str:
    """Durably retain source bytes and return their storage_path (an s3:// URI).

    Raises if object storage is not configured, rather than silently falling back to a
    local path the deployed service could never read back later.
    """
    settings = settings or get_settings()
    if not object_storage_configured(settings):
        raise RuntimeError(
            "Source archive object storage is not configured. Set "
            "SOURCE_ARCHIVE_BUCKET/SOURCE_ARCHIVE_ENDPOINT/SOURCE_ARCHIVE_ACCESS_KEY_ID/"
            "SOURCE_ARCHIVE_SECRET_ACCESS_KEY before archiving sources."
        )
    _client(settings).put_object(
        Bucket=settings.source_archive_bucket,
        Key=key,
        Body=body,
        ContentType=content_type,
    )
    return f"{_SCHEME}{settings.source_archive_bucket}/{key}"


def get_source_bytes(storage_path: str, *, settings: Settings | None = None) -> bytes:
    """Read back retained source bytes from an s3:// storage_path, or a legacy local path."""
    if storage_path.startswith(_SCHEME):
        settings = settings or get_settings()
        bucket, _, key = storage_path[len(_SCHEME) :].partition("/")
        response = _client(settings).get_object(Bucket=bucket, Key=key)
        return response["Body"].read()
    return Path(storage_path).expanduser().resolve(strict=True).read_bytes()


@contextlib.contextmanager
def source_local_copy(
    storage_path: str,
    *,
    suffix: str = ".pdf",
    settings: Settings | None = None,
) -> Iterator[Path]:
    """Yield a local filesystem Path to a source's bytes, for readers (e.g. pdfplumber)
    that require a real file. Materializes a temp file for s3:// paths and cleans it up
    afterward; returns the original path unchanged for legacy local paths."""
    if not storage_path.startswith(_SCHEME):
        yield Path(storage_path).expanduser().resolve(strict=True)
        return
    body = get_source_bytes(storage_path, settings=settings)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(body)
        temp_path = Path(handle.name)
    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)
