from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

_EXPECTED_JURISDICTIONS = 774
_SKIP_NAMES = {"", "local government councils", "total", "grand total"}


@dataclass(frozen=True)
class ExtractedLgaAllocation:
    state_name: str
    local_government_name: str
    net_statutory_allocation: Decimal | None
    deduction_amount: Decimal | None
    ecology_share: Decimal | None
    ecology_transfer: Decimal | None
    net_ecology_share: Decimal | None
    vat_amount: Decimal | None
    total_net_allocation: Decimal
    originals: dict[str, str | None]
    page: int


@dataclass(frozen=True)
class ExtractedLgaTable:
    rows: list[ExtractedLgaAllocation]
    warnings: list[str]
    requires_review: bool


@dataclass(frozen=True)
class _Panel:
    state: int
    lga: int
    net_statutory: int | None
    deduction: int | None
    ecology_share: int | None
    ecology_transfer: int | None
    net_ecology: int | None
    vat: int | None
    total_net: int
    start: int
    end: int


def _clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\n", " ")).strip()


def _slug_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _money(value: str | None) -> Decimal | None:
    text = _clean(value)
    if not text or text in {"-", "–", "—"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    normalized = text.strip("()₦N ").replace(",", "")
    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None
    return -amount if negative else amount


def _cell(row: list[str | None], index: int | None) -> str:
    if index is None or index < 0 or index >= len(row):
        return ""
    return _clean(row[index])


def _column_labels(table: list[list[str | None]]) -> list[str]:
    width = max((len(row) for row in table), default=0)
    labels: list[list[str]] = [[] for _ in range(width)]
    for row in table[:8]:
        for index in range(width):
            value = _cell(row, index)
            if value:
                labels[index].append(value)
    return [_slug_text(" ".join(parts)) for parts in labels]


def _find_index(labels: list[str], start: int, end: int, *needles: str) -> int | None:
    for index in range(start, end):
        label = labels[index]
        if all(needle in label for needle in needles):
            return index
    return None


def _resolve_panels(table: list[list[str | None]]) -> list[_Panel]:
    labels = _column_labels(table)
    lga_columns = [
        index for index, label in enumerate(labels) if "local government councils" in label
    ]
    if not lga_columns:
        return []

    panels: list[_Panel] = []
    for panel_number, lga_index in enumerate(lga_columns):
        start = 0 if panel_number == 0 else lga_columns[panel_number - 1] + 1
        end = lga_columns[panel_number + 1] if panel_number + 1 < len(lga_columns) else len(labels)
        state_index = next(
            (
                index
                for index in range(lga_index - 1, start - 1, -1)
                if labels[index] in {"state", "states"} or labels[index].startswith("state ")
            ),
            None,
        )
        total_net = _find_index(labels, lga_index + 1, end, "total net allocation")
        if state_index is None or total_net is None:
            continue
        panels.append(
            _Panel(
                state=state_index,
                lga=lga_index,
                net_statutory=_find_index(labels, lga_index + 1, end, "net statutory allocation"),
                deduction=_find_index(labels, lga_index + 1, end, "deduction"),
                ecology_share=_find_index(labels, lga_index + 1, end, "total share", "ecology"),
                ecology_transfer=_find_index(labels, lga_index + 1, end, "transfer", "ecology"),
                net_ecology=_find_index(labels, lga_index + 1, end, "net share", "ecology"),
                vat=_find_index(labels, lga_index + 1, end, "value added tax"),
                total_net=total_net,
                start=start,
                end=end,
            )
        )
    return panels


def _is_total_name(name: str) -> bool:
    folded = name.casefold().strip()
    return folded in _SKIP_NAMES or folded.endswith(" total")


def extract_oagf_table_iv(path: Path) -> ExtractedLgaTable:
    """Extract all observed LGA rows from OAGF Table IV, failing closed on coverage.

    OAGF Table IV is laid out as two side-by-side state/LGA panels on many pages.
    Column names, not fixed offsets, determine monetary meaning. The extractor
    therefore tolerates page-layout changes while refusing to infer missing cells.
    """
    import pdfplumber

    extracted: list[ExtractedLgaAllocation] = []
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = _slug_text(page.extract_text() or "")
            if "local government councils" not in page_text:
                continue
            tables = page.extract_tables() or []
            for table in tables:
                panels = _resolve_panels(table)
                for panel in panels:
                    current_state = ""
                    for raw in table:
                        state = _cell(raw, panel.state)
                        if (
                            state
                            and _slug_text(state) not in {"state", "states"}
                            and not state.casefold().endswith(" total")
                        ):
                            current_state = state
                        lga = _cell(raw, panel.lga)
                        total_original = _cell(raw, panel.total_net)
                        total_net = _money(total_original)
                        if (
                            not current_state
                            or _is_total_name(lga)
                            or total_net is None
                            or not re.search(r"[A-Za-z]", lga)
                        ):
                            continue

                        key = (_slug_text(current_state), _slug_text(lga))
                        if key in seen:
                            continue
                        seen.add(key)

                        originals = {
                            "net_statutory_allocation": _cell(raw, panel.net_statutory) or None,
                            "deduction_amount": _cell(raw, panel.deduction) or None,
                            "ecology_share": _cell(raw, panel.ecology_share) or None,
                            "ecology_transfer": _cell(raw, panel.ecology_transfer) or None,
                            "net_ecology_share": _cell(raw, panel.net_ecology) or None,
                            "vat_amount": _cell(raw, panel.vat) or None,
                            "total_net_allocation": total_original,
                        }
                        extracted.append(
                            ExtractedLgaAllocation(
                                state_name=current_state,
                                local_government_name=lga,
                                net_statutory_allocation=_money(
                                    originals["net_statutory_allocation"]
                                ),
                                deduction_amount=_money(originals["deduction_amount"]),
                                ecology_share=_money(originals["ecology_share"]),
                                ecology_transfer=_money(originals["ecology_transfer"]),
                                net_ecology_share=_money(originals["net_ecology_share"]),
                                vat_amount=_money(originals["vat_amount"]),
                                total_net_allocation=total_net,
                                originals=originals,
                                page=page.page_number,
                            )
                        )

    if len(extracted) != _EXPECTED_JURISDICTIONS:
        warnings.append(
            "OAGF Table IV coverage is incomplete or ambiguous: "
            f"expected {_EXPECTED_JURISDICTIONS} jurisdictions, extracted {len(extracted)}."
        )

    return ExtractedLgaTable(
        rows=extracted,
        warnings=warnings,
        requires_review=len(extracted) != _EXPECTED_JURISDICTIONS,
    )
