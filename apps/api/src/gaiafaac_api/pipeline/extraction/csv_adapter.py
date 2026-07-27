from __future__ import annotations

import csv
from pathlib import Path

from gaiafaac_api.pipeline.extraction.schema import (
    ALLOCATION_FIELDS,
    CellProvenance,
    ExtractedAllocationRow,
    ExtractedAllocationTable,
)

_EXTRA_COLUMNS = ("extraction_confidence", "data_label")


class GenericCsvAdapter:
    """Read a controlled CSV into the normalized schema, preserving original text."""

    name = "generic_csv"

    def supports(self, path: Path, mime_type: str) -> bool:
        return path.suffix.casefold() == ".csv" or mime_type == "text/csv"

    def extract(self, path: Path) -> ExtractedAllocationTable:
        rows: list[ExtractedAllocationRow] = []
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for source_row, raw in enumerate(reader, start=2):
                cells: dict[str, CellProvenance] = {}
                for field_name in (*ALLOCATION_FIELDS, *_EXTRA_COLUMNS):
                    if field_name in raw:
                        cells[field_name] = CellProvenance(
                            original_text=raw.get(field_name),
                            row=source_row,
                            column=field_name,
                        )
                rows.append(
                    ExtractedAllocationRow(
                        submitted_state=raw.get("state") or "",
                        reported_unit=raw.get("reported_unit"),
                        cells=cells,
                        source_row=source_row,
                    )
                )
        return ExtractedAllocationTable(
            source_organization="",
            adapter_name=self.name,
            rows=rows,
        )
