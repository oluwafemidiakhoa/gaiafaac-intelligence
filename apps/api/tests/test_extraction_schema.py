from pathlib import Path

import pytest

from gaiafaac_api.pipeline.extraction.base import (
    AllocationAdapter,
    ExtractionError,
    select_adapter,
)
from gaiafaac_api.pipeline.extraction.schema import (
    CellProvenance,
    ExtractedAllocationRow,
    ExtractedAllocationTable,
)


class _FakeAdapter:
    def __init__(self, name: str, suffix: str) -> None:
        self.name = name
        self._suffix = suffix

    def supports(self, path: Path, mime_type: str) -> bool:
        return path.suffix.casefold() == self._suffix

    def extract(self, path: Path) -> ExtractedAllocationTable:
        return ExtractedAllocationTable(
            source_organization="DEMO",
            adapter_name=self.name,
            rows=[
                ExtractedAllocationRow(
                    submitted_state="Lagos",
                    reported_unit="naira",
                    cells={"net_allocation": CellProvenance(original_text="900.00", row=2)},
                )
            ],
        )


def test_row_preserves_original_text() -> None:
    row = ExtractedAllocationRow(
        submitted_state="Kano",
        reported_unit="naira",
        cells={"gross_total": CellProvenance(original_text="2,000.00", page=3, row=5)},
    )
    assert row.original_text("gross_total") == "2,000.00"
    assert row.original_text("net_allocation") is None


def test_select_adapter_returns_first_supporting() -> None:
    adapters: list[AllocationAdapter] = [
        _FakeAdapter("csv", ".csv"),
        _FakeAdapter("xlsx", ".xlsx"),
    ]
    chosen = select_adapter(Path("report.xlsx"), "application/octet-stream", adapters)
    assert chosen.name == "xlsx"


def test_select_adapter_fails_closed() -> None:
    adapters: list[AllocationAdapter] = [_FakeAdapter("csv", ".csv")]
    with pytest.raises(ExtractionError):
        select_adapter(Path("report.pdf"), "application/pdf", adapters)
