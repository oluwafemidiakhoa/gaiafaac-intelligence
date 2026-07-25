from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from gaiafaac_api.pipeline.extraction.schema import ExtractedAllocationTable


class ExtractionError(Exception):
    """Raised when no adapter can handle a file or extraction fails closed."""


@runtime_checkable
class AllocationAdapter(Protocol):
    """Every adapter (CSV, Excel, OAGF PDF, ...) returns the same schema."""

    name: str

    def supports(self, path: Path, mime_type: str) -> bool: ...

    def extract(self, path: Path) -> ExtractedAllocationTable: ...


def select_adapter(
    path: Path, mime_type: str, adapters: list[AllocationAdapter]
) -> AllocationAdapter:
    """Return the first adapter that supports the file, else fail closed."""
    for adapter in adapters:
        if adapter.supports(path, mime_type):
            return adapter
    raise ExtractionError(f"No extraction adapter supports {path.name!r} (mime type {mime_type!r})")
