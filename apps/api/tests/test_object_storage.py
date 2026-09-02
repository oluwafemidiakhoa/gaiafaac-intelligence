import pytest

from gaiafaac_api.config import Settings
from gaiafaac_api.services.object_storage import (
    get_source_bytes,
    object_storage_configured,
    put_source_object,
    source_local_copy,
)


def _settings(**over) -> Settings:
    base = dict(
        source_archive_bucket="",
        source_archive_endpoint="",
        source_archive_access_key_id="",
        source_archive_secret_access_key="",
    )
    base.update(over)
    return Settings(**base)


def test_object_storage_configured_requires_all_fields():
    assert object_storage_configured(_settings()) is False
    assert (
        object_storage_configured(
            _settings(
                source_archive_bucket="b",
                source_archive_endpoint="https://example.com",
                source_archive_access_key_id="key",
                source_archive_secret_access_key="secret",
            )
        )
        is True
    )
    assert object_storage_configured(_settings(source_archive_bucket="only-bucket-set")) is False


def test_put_source_object_fails_closed_when_unconfigured():
    with pytest.raises(RuntimeError, match="not configured"):
        put_source_object(
            key="dmo/domestic/2026-03-31/abc.pdf",
            body=b"data",
            content_type="application/pdf",
            settings=_settings(),
        )


def test_get_source_bytes_reads_legacy_local_paths(tmp_path):
    path = tmp_path / "archived.pdf"
    path.write_bytes(b"%PDF-1.7\nlegacy local file")

    assert get_source_bytes(str(path)) == b"%PDF-1.7\nlegacy local file"


def test_source_local_copy_returns_the_same_path_for_legacy_local_paths(tmp_path):
    path = tmp_path / "archived.pdf"
    path.write_bytes(b"%PDF-1.7\nlegacy local file")

    with source_local_copy(str(path)) as copy:
        assert copy == path.expanduser().resolve()
        assert copy.read_bytes() == b"%PDF-1.7\nlegacy local file"

    # Legacy local paths are the durable copy itself and must not be deleted.
    assert path.exists()
