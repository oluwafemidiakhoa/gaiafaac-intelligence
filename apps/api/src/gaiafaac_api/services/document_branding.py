from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.units import mm

BRAND_NAME = "GAIA FISCAL INTELLIGENCE"
BRAND_SUBTITLE = "Governed Public-Finance Intelligence"
PAID_WATERMARK = BRAND_NAME
SAMPLE_WATERMARK = "SAMPLE — GAIA FISCAL INTELLIGENCE — NOT FOR RESALE"
SAMPLE_NOTICE = "SAMPLE / DEMONSTRATION ONLY / NOT FOR RELIANCE IN FORMAL DECISION-MAKING"


def _generated_label(value: object | None) -> str:
    if value in (None, ""):
        return datetime.now(UTC).isoformat()
    return str(value)


def brand_workbook(
    workbook: Workbook,
    *,
    sample: bool = False,
    order_id: str | None = None,
    jurisdiction: str | None = None,
    generated_at: object | None = None,
) -> None:
    """Apply persistent Gaia Fiscal Intelligence branding to every workbook sheet.

    XLSX has no native text-watermark primitive. The brand is therefore placed in
    print headers/footers on every worksheet, while the summary sheet remains visibly
    branded in normal workbook view.
    """

    watermark = SAMPLE_WATERMARK if sample else PAID_WATERMARK
    generated = _generated_label(generated_at)
    workbook.properties.title = f"{BRAND_NAME} governed public-finance deliverable"
    workbook.properties.creator = BRAND_NAME
    workbook.properties.description = (
        f"{SAMPLE_NOTICE}." if sample else "Governed public-finance intelligence deliverable."
    )

    for sheet in workbook.worksheets:
        sheet.oddHeader.center.text = watermark
        sheet.oddHeader.center.size = 12 if sample else 10
        sheet.oddHeader.center.font = "Arial,Bold"
        sheet.oddFooter.left.text = BRAND_NAME
        footer_middle = jurisdiction or BRAND_SUBTITLE
        sheet.oddFooter.center.text = footer_middle
        footer_parts = []
        if order_id:
            footer_parts.append(f"Order {order_id}")
        footer_parts.append(generated)
        sheet.oddFooter.right.text = " · ".join(footer_parts)


def draw_pdf_branding(
    canvas,
    doc,
    *,
    sample: bool = False,
    order_id: str | None = None,
    jurisdiction: str | None = None,
    generated_at: object | None = None,
) -> None:
    """Draw a diagonal watermark plus traceable footer on every PDF page."""

    watermark = SAMPLE_WATERMARK if sample else PAID_WATERMARK
    generated = _generated_label(generated_at)
    page_width, page_height = doc.pagesize

    canvas.saveState()
    with suppress(AttributeError):
        canvas.setFillAlpha(0.10 if sample else 0.055)
    canvas.setFillColor(colors.HexColor("#07594F"))
    canvas.setFont("Helvetica-Bold", 25 if sample else 31)
    canvas.translate(page_width / 2, page_height / 2)
    canvas.rotate(28)
    canvas.drawCentredString(0, 0, watermark)
    canvas.restoreState()

    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#65726F"))
    left = BRAND_NAME
    if jurisdiction:
        left = f"{left} · {jurisdiction}"
    canvas.drawString(14 * mm, 8 * mm, left)

    right_parts = []
    if order_id:
        right_parts.append(f"Order {order_id}")
    right_parts.append(generated)
    right_parts.append(f"Page {doc.page}")
    canvas.drawRightString(page_width - 14 * mm, 8 * mm, " · ".join(right_parts))
    canvas.restoreState()
