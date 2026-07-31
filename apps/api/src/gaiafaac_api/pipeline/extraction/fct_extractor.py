from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

# FCT totals are billions of Naira; any single revenue component (EMTL, exchange gain, etc.)
# is far smaller. The reconciliation tolerance is 1 Naira for rounding.
_TOLERANCE = Decimal("1")
_MIN_PLAUSIBLE_TOTAL = Decimal("1000000000")
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
        cleaned = token.replace(" ", "").replace(",", "").replace("(", "-").replace(")", "")
        try:
            numbers.append(Decimal(cleaned))
        except InvalidOperation:
            continue
    return numbers


def reconcile_fct_total(numbers: list[Decimal]) -> FctExtraction:
    """Verify the FCT total net allocation by arithmetic reconciliation, or refuse.

    OAGF **Table I** reports the FCT ("FCT-Abuja") on its net side with this column order:

        [statutory_gross, deduction, net_statutory, net_vat, emtl, exchange+ecology, total_net]

    The stated total is accepted **only** if
    ``net_statutory + net_vat + emtl + exchange == total_net`` (within tolerance) *and* the
    total is in the billions. A truncated row (too few columns) or one that does not reconcile
    is **refused** (``value=None``) — so an individual component such as EMTL can never be
    mistaken for the total. This is fail-closed by design: a value we cannot verify is left
    blank for human review, never guessed.
    """
    if len(numbers) < 7:
        return FctExtraction(
            None,
            "review_required",
            0.0,
            f"truncated FCT row ({len(numbers)} values found; need 7)",
        )
    net_statutory, net_vat, emtl, exchange, total = numbers[2:7]
    computed = net_statutory + net_vat + emtl + exchange
    if abs(computed - total) <= _TOLERANCE and total >= _MIN_PLAUSIBLE_TOTAL:
        return FctExtraction(
            total,
            "verified",
            1.0,
            "reconciled: net statutory + VAT + EMTL + exchange == total net",
        )
    return FctExtraction(
        None,
        "review_required",
        0.0,
        f"does not reconcile (computed {computed} vs stated {total})",
    )


def extract_fct_total_net(pdf_path: Path) -> FctExtraction:
    """Read and verify the FCT total net allocation from an OAGF disbursement PDF.

    Pure text is used (Table I lives on the first pages); the actual verification is delegated
    to :func:`reconcile_fct_total`, which refuses anything it cannot arithmetically confirm.
    """
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    for line in text.splitlines():
        upper = line.upper()
        if "FCT" in upper and "ABUJA" in upper:
            return reconcile_fct_total(parse_fct_line(line))
    return FctExtraction(None, "review_required", 0.0, "no FCT row found on page 1")
