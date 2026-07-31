from __future__ import annotations

from pathlib import Path

from gaiafaac_api.pipeline.extraction.fct_extractor import extract_fct_total_net
from gaiafaac_api.pipeline.extraction.schema import (
    CellProvenance,
    ExtractedAllocationRow,
    ExtractedAllocationTable,
)

# Rows in the OAGF state table that are not a state (subtotals, special beneficiaries).
# They are still surfaced to the importer, which flags unknown names for review rather
# than dropping them silently. "soku" is a recurring non-state artifact (a Sukuk-type line
# at the foot of Table III with a negligible value) and is skipped.
_SKIP_EXACT = {
    "",
    "s/n",
    "beneficiaries",
    "total",
    "grand total",
    "sub total",
    "sub-total",
    "soku",
}


class OagfPdfAdapter:
    """Extract the state-allocation table from an OAGF FAAC disbursement PDF.

    Targets 'Table III - Distribution of Revenue Allocation to State Governments',
    reading each state's Total Gross Amount and Total Net Amount as verbatim text.
    Deductions are derived downstream as gross - net. Pure text extraction only; a
    scanned/image PDF yields no rows and is flagged for human review.
    """

    name = "oagf_pdf"

    def supports(self, path: Path, mime_type: str) -> bool:
        return path.suffix.casefold() == ".pdf" or mime_type == "application/pdf"

    def extract(self, path: Path) -> ExtractedAllocationTable:
        import pdfplumber

        rows: list[ExtractedAllocationRow] = []
        warnings: list[str] = []
        with pdfplumber.open(path) as pdf:
            located = self._locate(pdf)
            if located is None:
                return ExtractedAllocationTable(
                    source_organization="Office of the Accountant-General of the Federation",
                    adapter_name=self.name,
                    rows=[],
                    warnings=[
                        "State distribution table (Table III) not found — the PDF may be scanned."
                    ],
                    requires_review=True,
                )
            page_no, table, cols = located
            state_i, gross_i, net_i, header_idx = cols
            for offset, raw in enumerate(table[header_idx + 1 :], start=header_idx + 2):
                state = _clean(raw[state_i])
                if state.casefold() in _SKIP_EXACT:
                    continue
                gross = _clean(raw[gross_i]) if gross_i is not None else None
                net = _clean(raw[net_i]) if net_i is not None else None
                rows.append(
                    ExtractedAllocationRow(
                        submitted_state=state,
                        reported_unit="naira",
                        cells={
                            "gross_total": CellProvenance(
                                gross,
                                page=page_no,
                                table=3,
                                row=offset,
                                column="Total Gross Amount",
                            ),
                            "net_allocation": CellProvenance(
                                net, page=page_no, table=3, row=offset, column="Total Net Amount"
                            ),
                        },
                        source_row=offset,
                    )
                )
        # FCT is not in the state table (Table III). Add it net-only from Table I via the
        # fail-closed reconciliation extractor; if it cannot be verified it is omitted (never
        # guessed), and the month will fail 37-jurisdiction completeness for human review.
        fct = extract_fct_total_net(path)
        if fct.value is not None:
            rows.append(
                ExtractedAllocationRow(
                    submitted_state="FCT",
                    reported_unit="naira",
                    cells={
                        "net_allocation": CellProvenance(
                            format(fct.value, "f"),
                            page=1,
                            table=1,
                            column="FCT Total Net Amount",
                        )
                    },
                )
            )
        else:
            warnings.append(f"FCT total not reconciled ({fct.note}); FCT omitted.")
        return ExtractedAllocationTable(
            source_organization="Office of the Accountant-General of the Federation",
            adapter_name=self.name,
            rows=rows,
            warnings=warnings,
        )

    @staticmethod
    def _locate(pdf):
        for page in pdf.pages[:8]:
            text = (page.extract_text() or "").upper()
            if "DISTRIBUTION OF REVENUE ALLOCATION TO STATE" not in text:
                continue
            for table in sorted(page.extract_tables(), key=len, reverse=True):
                cols = _resolve_columns(table)
                if cols is not None:
                    return page.page_number, table, cols
        return None


def _clean(value: str | None) -> str:
    return (value or "").replace("\n", " ").strip()


def _resolve_columns(table) -> tuple[int, int | None, int | None, int] | None:
    """Find the header row and the state / gross / net column indices by name."""
    for idx, row in enumerate(table[:4]):
        cells = [_clean(c).lower() for c in row]
        joined = " | ".join(cells)
        if "beneficiaries" in joined and "total net amount" in joined:
            state_i = next(i for i, c in enumerate(cells) if "beneficiaries" in c)
            gross_i = next((i for i, c in enumerate(cells) if "total gross amount" in c), None)
            net_i = next((i for i, c in enumerate(cells) if "total net amount" in c), None)
            return state_i, gross_i, net_i, idx
    return None
