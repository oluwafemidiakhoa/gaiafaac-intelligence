from __future__ import annotations

import hashlib
import json
from datetime import date

from gaiafaac_api.pipeline.oagf.storage import LocalArchiveStorage


def test_local_archive_uses_deterministic_hash_filename_and_deduplicates(tmp_path) -> None:
    storage = LocalArchiveStorage(tmp_path / "archive", tmp_path / "manifest.jsonl")
    arguments = {
        "content": b"%PDF fixture",
        "category_slug": "FAAC Report",
        "document_slug": "Disbursement June, 2026",
        "source_date": date(2026, 6, 1),
        "original_filename": "Disbursement-June-2026.pdf",
    }

    first = storage.archive(**arguments)
    second = storage.archive(**arguments)

    assert first.created is True
    assert second.created is False
    assert first.storage_path == second.storage_path
    assert "2026-06-01__disbursement-june-2026__" in first.storage_path
    assert first.sha256 in first.storage_path or first.sha256[:12] in first.storage_path


def test_manifest_is_canonical_jsonl(tmp_path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    storage = LocalArchiveStorage(tmp_path / "archive", manifest)

    storage.append_manifest({"z": 1, "a": "value"})

    assert json.loads(manifest.read_text()) == {"a": "value", "z": 1}
    assert manifest.read_text() == '{"a":"value","z":1}\n'


def test_local_archive_copies_a_prehashed_streamed_file(tmp_path) -> None:
    storage = LocalArchiveStorage(tmp_path / "archive", tmp_path / "manifest.jsonl")
    source = tmp_path / "download.source"
    source.write_bytes(b"%PDF streamed source")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()

    result = storage.archive_file(
        source_path=source,
        checksum=checksum,
        byte_length=source.stat().st_size,
        category_slug="annual-reports",
        document_slug="Audited Statement",
        source_date=date(2018, 12, 1),
        original_filename="statement.pdf",
    )

    assert result.created is True
    assert result.sha256 == checksum
    assert result.byte_length == source.stat().st_size


def test_archive_deduplicates_identical_bytes_across_titles_and_categories(tmp_path) -> None:
    storage = LocalArchiveStorage(tmp_path / "archive", tmp_path / "manifest.jsonl")
    first = storage.archive(
        content=b"%PDF same bytes",
        category_slug="faac-report",
        document_slug="First title",
        source_date=date(2026, 1, 1),
        original_filename="first.pdf",
    )
    second = storage.archive(
        content=b"%PDF same bytes",
        category_slug="treasury-circulars",
        document_slug="Second title",
        source_date=date(2025, 1, 1),
        original_filename="second.pdf",
    )

    assert second.created is False
    assert second.storage_path == first.storage_path
    assert len(list((tmp_path / "archive").rglob("*.pdf"))) == 1
