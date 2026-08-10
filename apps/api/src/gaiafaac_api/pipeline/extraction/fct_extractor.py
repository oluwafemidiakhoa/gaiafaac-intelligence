from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

# FCT totals are billions of Naira; individual revenue components are typically
# smaller. OAGF has used multiple Table I layouts over time. We only accept the
# value when the parsed row matches a known monetary-column count and the net
# components arithmetically reconcile to the stated total.
_TOLERANCE = Decimal("1")
_MIN_PLAUSIBLE_TOTAL = Decimal("1000000000")
_SUPPORTED_VALUE_COUNTS = {6, 7, 8}
_NUMBER = re.compile(r"\(?-?[\d ,]+\.\d{2}\)?")


@dataclass(frozen=True)
class FctExtraction:
    """Result of trying to read the FCT total net allocation from an OAGF report."""

    value: Decimal | None
    status: str  # "verified" | "review_required"
    confidence: float
    note: str


def parse_fct_line(line: str) -> list[Decimal]:
    """Parse every Naira figure out of a raw FCT table-row text line, in order."""
    numbers: list[Decimal] = []
    for token in _NUMBER.findall(line):
        cleaned = (
            token.replace(" ", "")
            .replace(",", "")
            .replace("(", "-")
            .replace(")", "")
        )
        try:
            numbers.append(Decimal(cleaned))
        except InvalidOperation:
            continue
    return numbers


def reconcile_fct_total(numbers: list[Decimal]) -> FctExtraction:
    """Verify the FCT total net allocation by arithmetic reconciliation, or refuse.

    OAGF Table I has used several FCT layouts. The first two monetary values are
    consistently statutory gross and deduction; the final monetary value is the
    stated total net allocation. Values between them are the net-side components.

    Known, source-verified layouts contain 6, 7, or 8 monetary values. For those
    layouts we accept the final value only when every parsed net-side component
    (``numbers[2:-1]``) sums to that total within one Naira and the total is in
    the billions.

    Unknown column counts, truncated rows, and non-reconciling rows are refused.
    This stays fail-closed: a revenue component is never substituted for the
    total and a future layout must reconcile before it can enter the ledger.
    """
    count = len(numbers)
    if count not in _SUPPORTED_VALUE_COUNTS:
        supported = ", ".join(str(value) for value in sorted(_SUPPORTED_VALUE_COUNTS))
        return FctExtraction(
            None,
            "review_required",
            0.0,
            f"unsupported FCT row layout ({count} values found; supported: {supported})",
        )

    components = numbers[2:-1]
    total = numbers[-1]
    computed = sum(components, Decimal("0"))

    if abs(computed - total) <= _TOLERANCE and total >= _MIN_PLAUSIBLE_TOTAL:
        return FctExtraction(
            total,
            "verified",
            1.0,
            f"reconciled {count}-value layout: net components sum to total net",
        )

    return FctExtraction(
        None,
        "review_required",
        0.0,
        f"does not reconcile (computed {computed} vs stated {total})",
    )


def extract_fct_total_net(pdf_path: Path) -> FctExtraction:
    """Read and verify the FCT total net allocation from an OAGF disbursement PDF.

    Pure text is used (Table I lives on the first pages); the actual verification
    is delegated to :func:`reconcile_fct_total`, which refuses anything it cannot
    arithmetically confirm.
    """
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    for line in text.splitlines():
        upper = line.upper()
        if "FCT" in upper and "ABUJA" in upper:
            return reconcile_fct_total(parse_fct_line(line))
    return FctExtraction(None, "review_required", 0.0, "no FCT row found on page 1")
