from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import shutil
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.oagf_revision_models import OagfArchiveObject


@dataclass(frozen=True)
class ArchivedObject:
    storage_path: str
    sha256: str
    byte_length: int
    created: bool


class ArchiveStorage(Protocol):
    def archive(
        self,
        *,
        content: bytes,
        category_slug: str,
        document_slug: str,
        source_date: date,
        original_filename: str,
    ) -> ArchivedObject: ...

    def archive_file(
        self,
        *,
        source_path: Path,
        checksum: str,
        byte_length: int,
        category_slug: str,
        document_slug: str,
        source_date: date,
        original_filename: str,
    ) -> ArchivedObject: ...

    def append_manifest(self, payload: dict[str, Any]) -> None: ...


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "document"


class DatabaseArchiveStorage:
    """Content-addressed durable archive stored in the production database.

    The discovery ledger remains the canonical event manifest; this storage class
    only retains exact bytes and therefore intentionally has a no-op manifest hook.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _storage_path(checksum: str) -> str:
        return f"/oagf-db-archive/{checksum}"

    def _archive_bytes(
        self,
        *,
        content: bytes,
        checksum: str,
        category_slug: str,
        document_slug: str,
        source_date: date,
        original_filename: str,
    ) -> ArchivedObject:
        actual = sha256_bytes(content)
        if actual != checksum:
            raise RuntimeError("OAGF archive checksum mismatch")
        existing = self.session.scalar(
            select(OagfArchiveObject).where(OagfArchiveObject.sha256 == checksum)
        )
        if existing is not None:
            if existing.byte_length != len(content) or bytes(existing.content) != content:
                raise RuntimeError("OAGF archive hash collision")
            return ArchivedObject(
                self._storage_path(checksum), checksum, existing.byte_length, False
            )

        content_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"
        archived = OagfArchiveObject(
            sha256=checksum,
            content=content,
            byte_length=len(content),
            content_type=content_type,
            original_filename=original_filename,
            metadata_json={
                "category_slug": category_slug,
                "document_slug": document_slug,
                "source_date": source_date.isoformat(),
            },
        )
        self.session.add(archived)
        self.session.flush()
        return ArchivedObject(self._storage_path(checksum), checksum, len(content), True)

    def archive(
        self,
        *,
        content: bytes,
        category_slug: str,
        document_slug: str,
        source_date: date,
        original_filename: str,
    ) -> ArchivedObject:
        return self._archive_bytes(
            content=content,
            checksum=sha256_bytes(content),
            category_slug=category_slug,
            document_slug=document_slug,
            source_date=source_date,
            original_filename=original_filename,
        )

    def archive_file(
        self,
        *,
        source_path: Path,
        checksum: str,
        byte_length: int,
        category_slug: str,
        document_slug: str,
        source_date: date,
        original_filename: str,
    ) -> ArchivedObject:
        if source_path.stat().st_size != byte_length:
            raise RuntimeError("OAGF archive byte-length mismatch")
        content = source_path.read_bytes()
        return self._archive_bytes(
            content=content,
            checksum=checksum,
            category_slug=category_slug,
            document_slug=document_slug,
            source_date=source_date,
            original_filename=original_filename,
        )

    def append_manifest(self, payload: dict[str, Any]) -> None:
        # OagfDiscoveryRecord/OagfSyncRun are the durable event manifest in DB mode.
        return None


class LocalArchiveStorage:
    def __init__(
        self,
        root: Path = Path("data/oagf/archive"),
        manifest_path: Path = Path("data/oagf/manifest.jsonl"),
    ) -> None:
        self.root = root
        self.manifest_path = manifest_path

    def manifest_document_count(self) -> int:
        if not self.manifest_path.exists():
            return 0
        urls: set[str] = set()
        for line in self.manifest_path.read_text(encoding="utf-8").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            url = payload.get("document_url")
            if isinstance(url, str):
                urls.add(url)
        return len(urls)

    def _existing_hash_object(self, checksum: str) -> Path | None:
        if not self.root.exists():
            return None
        for candidate in self.root.rglob(f"*__{checksum[:12]}.*"):
            if candidate.is_file() and sha256_path(candidate) == checksum:
                return candidate
        return None

    def archive(
        self,
        *,
        content: bytes,
        category_slug: str,
        document_slug: str,
        source_date: date,
        original_filename: str,
    ) -> ArchivedObject:
        checksum = sha256_bytes(content)
        existing = self._existing_hash_object(checksum)
        if existing is not None:
            return ArchivedObject(str(existing), checksum, len(content), False)
        suffix = PurePosixPath(original_filename).suffix.lower() or ".bin"
        filename = f"{source_date.isoformat()}__{safe_slug(document_slug)}__{checksum[:12]}{suffix}"
        destination = self.root / safe_slug(category_slug) / str(source_date.year) / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        created = not destination.exists()
        if created:
            destination.write_bytes(content)
        elif sha256_path(destination) != checksum:
            raise RuntimeError(f"Archive collision at {destination}")
        return ArchivedObject(str(destination), checksum, len(content), created)

    def archive_file(
        self,
        *,
        source_path: Path,
        checksum: str,
        byte_length: int,
        category_slug: str,
        document_slug: str,
        source_date: date,
        original_filename: str,
    ) -> ArchivedObject:
        existing = self._existing_hash_object(checksum)
        if existing is not None:
            return ArchivedObject(str(existing), checksum, byte_length, False)
        suffix = PurePosixPath(original_filename).suffix.lower() or ".bin"
        filename = f"{source_date.isoformat()}__{safe_slug(document_slug)}__{checksum[:12]}{suffix}"
        destination = self.root / safe_slug(category_slug) / str(source_date.year) / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        created = not destination.exists()
        if created:
            shutil.copyfile(source_path, destination)
        elif sha256_path(destination) != checksum:
            raise RuntimeError(f"Archive collision at {destination}")
        return ArchivedObject(str(destination), checksum, byte_length, created)

    def append_manifest(self, payload: dict[str, Any]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        with self.manifest_path.open("a", encoding="utf-8", newline="\n") as manifest:
            manifest.write(f"{line}\n")
