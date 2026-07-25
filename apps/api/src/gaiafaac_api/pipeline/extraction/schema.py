from __future__ import annotations

from dataclasses import dataclass, field

# Canonical allocation fields an adapter may populate. Values are always carried
# as ORIGINAL TEXT with provenance; parsing to Decimal happens downstream so no
# monetary value is ever silently inferred at the extraction boundary.
ALLOCATION_FIELDS = ("gross_total", "total_deductions", "net_allocation")


@dataclass(frozen=True)
class CellProvenance:
    """Where an extracted value came from, plus its verbatim original text."""

    original_text: str | None
    page: int | None = None
    table: int | None = None
    row: int | None = None
    column: str | None = None


@dataclass(frozen=True)
class ExtractedAllocationRow:
    """One state's raw extracted allocation, before normalization/parsing."""

    submitted_state: str
    reported_unit: str | None
    cells: dict[str, CellProvenance]
    source_row: int | None = None

    def original_text(self, field_name: str) -> str | None:
        cell = self.cells.get(field_name)
        return cell.original_text if cell is not None else None


@dataclass(frozen=True)
class ExtractedAllocationTable:
    """Adapter output: the single normalized schema all adapters return."""

    source_organization: str
    adapter_name: str
    rows: list[ExtractedAllocationRow]
    warnings: list[str] = field(default_factory=list)
    requires_review: bool = False
