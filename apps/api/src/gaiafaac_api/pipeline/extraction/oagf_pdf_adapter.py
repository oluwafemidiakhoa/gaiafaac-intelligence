from __future__ import annotations

from pathlib import Path

from gaiafaac_api.pipeline.extraction.fct_extractor import extract_fct_total_net
from gaiafaac_api.pipeline.extraction.schema import (
    CellProvenance,
    ExtractedAllocationRow,
    ExtractedAllocationTable,
)


# Rows in the OAGF state table that are not states.
#
# Subtotals and table labels must never become allocations. Unknown names that are
# not explicitly skipped still flow to the governed importer, which will flag them
# for human review instead of silently guessing.
#
# "soku" is a recurring non-state artifact at the foot of some historical OAGF
# tables and is intentionally skipped.
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
    """Extract state allocations from an OAGF FAAC disbursement PDF.

    The adapter targets Table III, "Distribution of Revenue Allocation to State
    Governments", and extracts each state's reported gross and net allocation.

    OAGF has used multiple compatible Table III layouts over time:

    - "Total Gross Amount" / "Total Net Amount"
    - "Total Gross Allocation" / "Total Net Allocation"
    - multi-row headers whose named header may appear several rows into the table
    - reports where Table III appears after page 8

    Deductions are derived downstream as gross minus net.

    FCT is handled separately because it is not represented in Table III on the
    same basis as the 36 states. Its net amount is extracted from Table I using
    the fail-closed FCT reconciler. If FCT cannot be reconciled, it is omitted and
    the governed validation layer blocks 37-jurisdiction completeness.
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
                    source_organization=("Office of the Accountant-General of the Federation"),
                    adapter_name=self.name,
                    rows=[],
                    warnings=[
                        "State distribution table (Table III) could not be "
                        "resolved from the PDF layout."
                    ],
                    requires_review=True,
                )

            page_no, table, cols = located
            state_i, gross_i, net_i, header_idx = cols

            header = table[header_idx]

            gross_column_name = (
                _clean(header[gross_i])
                if gross_i is not None and gross_i < len(header)
                else "Total Gross Amount"
            )

            net_column_name = (
                _clean(header[net_i])
                if net_i is not None and net_i < len(header)
                else "Total Net Amount"
            )

            for offset, raw in enumerate(
                table[header_idx + 1 :],
                start=header_idx + 2,
            ):
                state = _cell(raw, state_i)

                if state.casefold() in _SKIP_EXACT:
                    continue

                gross = _cell(raw, gross_i) if gross_i is not None else None
                net = _cell(raw, net_i) if net_i is not None else None

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
                                column=gross_column_name,
                            ),
                            "net_allocation": CellProvenance(
                                net,
                                page=page_no,
                                table=3,
                                row=offset,
                                column=net_column_name,
                            ),
                        },
                        source_row=offset,
                    )
                )

        # FCT is not represented in Table III on the same basis as the states.
        # Extract only its reconciled net total from Table I.
        #
        # This deliberately remains fail-closed. A value is never guessed.
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
            source_organization=("Office of the Accountant-General of the Federation"),
            adapter_name=self.name,
            rows=rows,
            warnings=warnings,
        )

    @staticmethod
    def _locate(pdf):
        """Locate the OAGF state-distribution table anywhere in the PDF.

        Older logic searched only the first eight pages. OAGF reports can place
        Table III later in the document, so all pages are considered.

        A page must still contain the explicit state-distribution title before
        any extracted table on that page is considered. This prevents accidental
        selection of similarly shaped local-government or summary tables.
        """

        for page in pdf.pages:
            text = (page.extract_text() or "").upper()

            if "DISTRIBUTION OF REVENUE ALLOCATION TO STATE" not in text:
                continue

            tables = page.extract_tables() or []

            for table in sorted(tables, key=len, reverse=True):
                cols = _resolve_columns(table)

                if cols is not None:
                    return page.page_number, table, cols

        return None


def _clean(value: str | None) -> str:
    """Normalize extracted PDF cell text without altering monetary content."""

    return (value or "").replace("\n", " ").strip()


def _cell(row, index: int) -> str:
    """Safely return a cleaned cell from a pdfplumber table row."""

    if index < 0 or index >= len(row):
        return ""

    return _clean(row[index])


def _resolve_columns(
    table,
) -> tuple[int, int | None, int | None, int] | None:
    """Resolve state, gross, and net columns from known OAGF Table III headers.

    OAGF uses multi-row table headers and has changed terminology across reports.
    The named header can therefore occur several rows after the beginning of the
    extracted table.

    Gross is optional because the governed pipeline can accept net-only FCT data,
    but a Table III state table must contain a state/beneficiary column and a net
    allocation column.
    """

    for idx, row in enumerate(table[:10]):
        cells = [_clean(cell).lower() for cell in row]
        joined = " | ".join(cells)

        if "beneficiaries" not in joined:
            continue

        state_i = next(
            (i for i, cell in enumerate(cells) if "beneficiaries" in cell),
            None,
        )

        gross_i = next(
            (
                i
                for i, cell in enumerate(cells)
                if ("total gross amount" in cell or "total gross allocation" in cell)
            ),
            None,
        )

        net_i = next(
            (
                i
                for i, cell in enumerate(cells)
                if ("total net amount" in cell or "total net allocation" in cell)
            ),
            None,
        )

        if state_i is not None and net_i is not None:
            return state_i, gross_i, net_i, idx

    return None
