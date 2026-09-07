from __future__ import annotations

import io
from decimal import Decimal, InvalidOperation
from typing import Any
from xml.sax.saxutils import escape

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from gaiafaac_api.config import get_settings
from gaiafaac_api.services.document_branding import (
    BRAND_NAME,
    BRAND_SUBTITLE,
    SAMPLE_NOTICE,
    brand_workbook,
    draw_pdf_branding,
)
from gaiafaac_api.services.one_time_exports import (
    _DARK_TEAL,
    _LIGHT_AMBER,
    _LIGHT_TEAL,
    _PDF_MIME,
    _TEAL,
    _XLSX_MIME,
    _display,
    _flatten_mapping,
    _pdf_text,
    _table_rows,
)
from gaiafaac_api.services.one_time_exports import (
    build_one_time_excel as _build_legacy_excel,
)
from gaiafaac_api.services.project_receipts import canonical_artifact_sha256

_CURRENCY_FORMAT = '₦#,##0.00'
_PERCENT_FORMAT = '0.00%'


def _filename(product_code: str, purchase_id: str, suffix: str, *, sample: bool) -> str:
    product = product_code.replace("_", "-")
    if sample:
        return f"gaia-fiscal-intelligence-sample-{product}.{suffix}"
    short_id = "".join(character for character in purchase_id if character.isalnum())[:12]
    return f"gaia-fiscal-intelligence-{product}-{short_id or 'order'}.{suffix}"


def _verification_url(purchase_id: str, *, sample: bool) -> str | None:
    if sample:
        return None
    base = get_settings().customer_app_url.rstrip("/")
    return f"{base}/verify/project/{purchase_id}"


def _money(value: object) -> str:
    if value in (None, ""):
        return "Not available"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return _display(value)
    return f"₦{amount:,.2f}"


def _percent(value: object) -> str:
    if value in (None, ""):
        return "Not available"
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return _display(value)
    return f"{number:,.2f}%"


def _decision_packet(artifact: dict[str, Any]) -> dict[str, Any] | None:
    packet = artifact.get("decision_packet")
    return packet if isinstance(packet, dict) else None


def _write_section_header(sheet, row: int, title: str) -> int:
    sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
    cell = sheet.cell(row=row, column=1, value=title)
    cell.font = Font(size=11, bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor=_TEAL)
    cell.alignment = Alignment(vertical="center")
    sheet.row_dimensions[row].height = 22
    return row + 1


def _rebuild_decision_pack_summary(
    workbook,
    *,
    artifact: dict[str, Any],
    amount_naira: str,
    sample: bool,
    jurisdiction: str | None,
) -> None:
    packet = _decision_packet(artifact)
    if packet is None:
        return

    sheet = workbook["Summary"]
    for merged_range in list(sheet.merged_cells.ranges):
        sheet.unmerge_cells(str(merged_range))
    sheet.delete_rows(1, sheet.max_row)

    sheet.merge_cells("A1:D1")
    sheet["A1"] = BRAND_NAME
    sheet["A1"].font = Font(size=20, bold=True, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor=_DARK_TEAL)
    sheet["A1"].alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 34

    sheet.merge_cells("A2:D2")
    sheet["A2"] = "Decision Pack · Executive Fiscal Evidence Summary"
    sheet["A2"].font = Font(size=12, bold=True, color=_TEAL)
    sheet["A2"].fill = PatternFill("solid", fgColor=_LIGHT_TEAL)

    row = 4
    if sample:
        sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        sheet.cell(row=row, column=1, value=SAMPLE_NOTICE)
        sheet.cell(row=row, column=1).font = Font(size=10, bold=True, color="FFFFFF")
        sheet.cell(row=row, column=1).fill = PatternFill("solid", fgColor="9C2A1B")
        sheet.cell(row=row, column=1).alignment = Alignment(vertical="center", wrap_text=True)
        sheet.row_dimensions[row].height = 26
        row += 2

    row = _write_section_header(sheet, row, "Decision overview")
    overview = [
        ("Jurisdiction", packet.get("state_name") or jurisdiction or "Not declared"),
        ("Evidence year", packet.get("year")),
        ("Coverage", packet.get("coverage_label")),
        ("Evidence status", packet.get("evidence_status")),
        ("Published months", packet.get("months_published")),
        (
            "Commercial sample value" if sample else "Intelligence package value",
            _money(amount_naira),
        ),
    ]
    for label, value in overview:
        sheet.cell(row=row, column=1, value=label).font = Font(bold=True, color=_TEAL)
        sheet.cell(row=row, column=2, value=value)
        row += 1

    row += 1
    row = _write_section_header(sheet, row, "Key fiscal measures")
    metrics = [
        ("Gross allocation", _money(packet.get("annual_gross"))),
        ("Total deductions", _money(packet.get("annual_deductions"))),
        ("Net allocation", _money(packet.get("annual_net"))),
        ("Deduction burden", _percent(packet.get("deduction_burden_pct"))),
        ("Net retention", _percent(packet.get("net_retention_pct"))),
        ("Momentum", packet.get("momentum")),
        ("Momentum change", _percent(packet.get("momentum_pct"))),
        ("Volatility", packet.get("volatility")),
        ("Volatility CV", _percent(packet.get("volatility_cv_pct"))),
    ]
    for label, value in metrics:
        sheet.cell(row=row, column=1, value=label).font = Font(bold=True, color=_TEAL)
        sheet.cell(row=row, column=2, value=value)
        row += 1

    row += 1
    row = _write_section_header(sheet, row, "Evidence boundary and interpretation")
    notes = [
        (
            "What this product does",
            "Freezes governed fiscal evidence for a defined jurisdiction and period, preserves source provenance, and applies deterministic fiscal calculations.",
        ),
        (
            "IGR evidence",
            packet.get("igr_note") or "No IGR note was supplied for this evidence boundary.",
        ),
        (
            "Interpretation boundary",
            packet.get("disclaimer")
            or "This is an evidence dossier, not a credit rating, investment recommendation, or predictive assessment.",
        ),
    ]
    for label, value in notes:
        sheet.cell(row=row, column=1, value=label).font = Font(bold=True, color=_TEAL)
        value_cell = sheet.cell(row=row, column=2, value=value)
        value_cell.alignment = Alignment(vertical="top", wrap_text=True)
        sheet.row_dimensions[row].height = 42
        row += 1

    sheet.column_dimensions["A"].width = 28
    sheet.column_dimensions["B"].width = 94
    sheet.column_dimensions["C"].width = 14
    sheet.column_dimensions["D"].width = 14
    for row_cells in sheet.iter_rows(min_row=1, max_row=sheet.max_row, min_col=1, max_col=4):
        for cell in row_cells:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    sheet.freeze_panes = "A4"
    sheet.sheet_view.showGridLines = False


def _polish_months_sheet(workbook) -> None:
    if "Months" not in workbook.sheetnames:
        return
    sheet = workbook["Months"]
    labels = {
        "revenue_month": "Revenue month",
        "reporting_label": "Official reporting label",
        "gross_total": "Gross allocation (₦)",
        "total_deductions": "Deductions (₦)",
        "net_allocation": "Net allocation (₦)",
        "reconciliation_status": "Reconciliation",
        "proof_id": "Gaia proof ID",
        "proof_path": "Proof path",
        "source_organization": "Official source",
        "source_sha256": "Source SHA-256",
        "human_verified": "Human verified",
    }
    header_by_column: dict[int, str] = {}
    for cell in sheet[1]:
        original = str(cell.value or "")
        header_by_column[cell.column] = original
        cell.value = labels.get(original, original.replace("_", " ").title())
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=_TEAL)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    sheet.row_dimensions[1].height = 30

    money_columns = {
        column
        for column, original in header_by_column.items()
        if original in {"gross_total", "total_deductions", "net_allocation"}
    }
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            original = header_by_column.get(cell.column, "")
            if cell.column in money_columns and cell.value not in (None, ""):
                try:
                    cell.value = float(Decimal(str(cell.value)))
                    cell.number_format = _CURRENCY_FORMAT
                except (InvalidOperation, ValueError):
                    pass
            if original == "human_verified":
                cell.value = "Yes" if bool(cell.value) else "No"
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    widths = {
        1: 14,
        2: 38,
        3: 20,
        4: 20,
        5: 20,
        6: 16,
        7: 24,
        8: 32,
        9: 40,
        10: 28,
        11: 16,
    }
    for column, width in widths.items():
        sheet.column_dimensions[sheet.cell(row=1, column=column).column_letter].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    sheet.sheet_view.showGridLines = False


def build_one_time_excel(
    *,
    purchase_id: str,
    product_code: str,
    amount_naira: str,
    currency: str,
    completed_at: object,
    artifact: dict[str, Any],
    sample: bool = False,
    jurisdiction: str | None = None,
) -> tuple[str, str, bytes]:
    _legacy_filename, _media_type, body = _build_legacy_excel(
        purchase_id=purchase_id,
        product_code=product_code,
        amount_naira=amount_naira,
        currency=currency,
        completed_at=completed_at,
        artifact=artifact,
    )
    workbook = load_workbook(io.BytesIO(body))

    if product_code == "decision_pack" and _decision_packet(artifact):
        _rebuild_decision_pack_summary(
            workbook,
            artifact=artifact,
            amount_naira=amount_naira,
            sample=sample,
            jurisdiction=jurisdiction,
        )
        _polish_months_sheet(workbook)
    else:
        summary = workbook["Summary"]
        summary["A1"] = BRAND_NAME
        summary["A1"].font = Font(size=18, bold=True, color="FFFFFF")
        summary["A1"].fill = PatternFill("solid", fgColor=_DARK_TEAL)
        summary["A2"] = BRAND_SUBTITLE
        if sample:
            summary["A3"] = SAMPLE_NOTICE
            summary["A3"].font = Font(size=10, bold=True, color="9C2A1B")

    artifact_sha256 = canonical_artifact_sha256(artifact)
    verification_url = _verification_url(purchase_id, sample=sample)
    brand_workbook(
        workbook,
        sample=sample,
        order_id=None if sample else purchase_id,
        jurisdiction=jurisdiction,
        generated_at=artifact.get("captured_at"),
        artifact_sha256=artifact_sha256,
        verification_url=verification_url,
    )

    buffer = io.BytesIO()
    workbook.save(buffer)
    return (
        _filename(product_code, purchase_id, "xlsx", sample=sample),
        _XLSX_MIME,
        buffer.getvalue(),
    )


def _metric_table(packet: dict[str, Any], body_style) -> Table:
    rows = [
        ["Gross allocation", _money(packet.get("annual_gross")), "Momentum", _display(packet.get("momentum"))],
        ["Deductions", _money(packet.get("annual_deductions")), "Momentum change", _percent(packet.get("momentum_pct"))],
        ["Net allocation", _money(packet.get("annual_net")), "Volatility", _display(packet.get("volatility"))],
        ["Deduction burden", _percent(packet.get("deduction_burden_pct")), "Volatility CV", _percent(packet.get("volatility_cv_pct"))],
        ["Net retention", _percent(packet.get("net_retention_pct")), "Evidence status", _display(packet.get("evidence_status"))],
    ]
    table = Table(
        [[Paragraph(f"<b>{escape(str(a))}</b>", body_style), Paragraph(_pdf_text(b), body_style), Paragraph(f"<b>{escape(str(c))}</b>", body_style), Paragraph(_pdf_text(d), body_style)] for a, b, c, d in rows],
        colWidths=[36 * mm, 62 * mm, 36 * mm, 62 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(f"#{_LIGHT_TEAL}")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor(f"#{_LIGHT_TEAL}")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D7D3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _decision_pack_months_table(packet: dict[str, Any], small_style) -> Table | None:
    months = packet.get("months")
    if not isinstance(months, list) or not months:
        return None
    header = ["Month", "Gross allocation", "Deductions", "Net allocation", "Status", "Proof ID"]
    rows: list[list[object]] = [
        [Paragraph(f"<b>{escape(item)}</b>", small_style) for item in header]
    ]
    for month in months:
        if not isinstance(month, dict):
            continue
        rows.append(
            [
                Paragraph(_pdf_text(month.get("revenue_month")), small_style),
                Paragraph(_pdf_text(_money(month.get("gross_total"))), small_style),
                Paragraph(_pdf_text(_money(month.get("total_deductions"))), small_style),
                Paragraph(_pdf_text(_money(month.get("net_allocation"))), small_style),
                Paragraph(_pdf_text(month.get("reconciliation_status")), small_style),
                Paragraph(_pdf_text(month.get("proof_id")), small_style),
            ]
        )
    table = Table(rows, colWidths=[26 * mm, 42 * mm, 38 * mm, 42 * mm, 31 * mm, 58 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{_TEAL}")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#D5E0DD")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAF9")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build_one_time_pdf(
    *,
    purchase_id: str,
    product_code: str,
    amount_naira: str,
    currency: str,
    completed_at: object,
    artifact: dict[str, Any],
    sample: bool = False,
    jurisdiction: str | None = None,
) -> tuple[str, str, bytes]:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=15 * mm,
        title=f"{BRAND_NAME} governed public-finance deliverable",
        author=BRAND_NAME,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "GaiaFiscalTitle",
        parent=styles["Title"],
        textColor=colors.HexColor(f"#{_DARK_TEAL}"),
        fontSize=24,
        leading=28,
        spaceAfter=1.5 * mm,
    )
    subtitle_style = ParagraphStyle(
        "GaiaFiscalSubtitle",
        parent=styles["Heading2"],
        textColor=colors.HexColor(f"#{_TEAL}"),
        fontSize=12,
        leading=15,
        spaceAfter=2.5 * mm,
    )
    section_style = ParagraphStyle(
        "GaiaFiscalSection",
        parent=styles["Heading2"],
        textColor=colors.HexColor(f"#{_TEAL}"),
        fontSize=12,
        leading=15,
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
    )
    body_style = ParagraphStyle(
        "GaiaFiscalBody",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#263633"),
    )
    small_style = ParagraphStyle(
        "GaiaFiscalSmall",
        parent=body_style,
        fontSize=6.8,
        leading=8.4,
    )
    notice_style = ParagraphStyle(
        "GaiaFiscalSampleNotice",
        parent=body_style,
        textColor=colors.HexColor("#9C2A1B"),
        fontSize=9,
        leading=11,
        spaceAfter=2.5 * mm,
    )

    artifact_sha256 = canonical_artifact_sha256(artifact)
    verification_url = _verification_url(purchase_id, sample=sample)
    packet = _decision_packet(artifact)
    story: list[object] = [
        Paragraph(BRAND_NAME, title_style),
        Paragraph(
            "Decision Pack · Source-linked fiscal evidence for institutional review"
            if product_code == "decision_pack"
            else BRAND_SUBTITLE,
            subtitle_style,
        ),
    ]
    if sample:
        story.append(Paragraph(f"<b>{escape(SAMPLE_NOTICE)}</b>", notice_style))

    if product_code == "decision_pack" and packet is not None:
        overview_rows = [
            ["Jurisdiction", packet.get("state_name") or jurisdiction],
            ["Evidence year", packet.get("year")],
            ["Coverage", packet.get("coverage_label")],
            ["Published months", packet.get("months_published")],
            ["Sample value" if sample else "Package value", _money(amount_naira)],
        ]
        overview = Table(
            [[Paragraph(f"<b>{escape(str(label))}</b>", body_style), Paragraph(_pdf_text(value), body_style)] for label, value in overview_rows],
            colWidths=[44 * mm, 88 * mm],
        )
        overview.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(f"#{_LIGHT_AMBER}")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDD3AE")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.extend(
            [
                Paragraph("Executive snapshot", section_style),
                overview,
                Spacer(1, 2.5 * mm),
                _metric_table(packet, body_style),
                Spacer(1, 3 * mm),
                Paragraph("Evidence boundary", section_style),
                Paragraph(
                    _pdf_text(
                        packet.get("igr_note")
                        or "Gaia reports only evidence that is available and governed for the declared boundary."
                    ),
                    body_style,
                ),
                Spacer(1, 2 * mm),
                Paragraph(
                    "This Decision Pack is a governed evidence dossier. It preserves provenance and deterministic calculations; it is not a credit rating, investment recommendation, or predictive assessment.",
                    body_style,
                ),
                PageBreak(),
                Paragraph("Monthly governed evidence", section_style),
            ]
        )
        months_table = _decision_pack_months_table(packet, small_style)
        if months_table is not None:
            story.append(months_table)
        story.extend(
            [
                Spacer(1, 3 * mm),
                Paragraph("Provenance register", section_style),
            ]
        )
        months = packet.get("months") if isinstance(packet.get("months"), list) else []
        provenance_rows = [["Month", "Official source", "Source SHA-256", "Human verified"]]
        for month in months:
            if isinstance(month, dict):
                provenance_rows.append(
                    [
                        _display(month.get("revenue_month")),
                        _display(month.get("source_organization")),
                        _display(month.get("source_sha256")),
                        "Yes" if month.get("human_verified") else "No",
                    ]
                )
        provenance = Table(
            [
                [Paragraph(f"<b>{escape(str(value))}</b>", small_style) if row_index == 0 else Paragraph(_pdf_text(value), small_style) for value in row]
                for row_index, row in enumerate(provenance_rows)
            ],
            colWidths=[28 * mm, 82 * mm, 104 * mm, 26 * mm],
            repeatRows=1,
        )
        provenance.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{_TEAL}")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#D5E0DD")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(provenance)
    else:
        order_rows = [
            ["Sample reference" if sample else "Order ID", purchase_id],
            ["Product", product_code.replace("_", " ").title()],
            ["Illustrative package value" if sample else "Amount paid", _money(amount_naira)],
            ["Payment", "Not applicable — demonstration sample" if sample else _display(completed_at)],
            ["Artifact schema", _display(artifact.get("schema"))],
            ["Evidence captured", _display(artifact.get("captured_at"))],
            ["Artifact SHA-256", artifact_sha256],
            ["Verification", verification_url or "Sample document — no paid receipt verification"],
        ]
        order_table = Table(
            [[Paragraph(f"<b>{escape(label)}</b>", body_style), Paragraph(_pdf_text(value), body_style)] for label, value in order_rows],
            colWidths=[54 * mm, 184 * mm],
        )
        order_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(f"#{_LIGHT_TEAL}")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D7D3")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.extend([order_table, Spacer(1, 3 * mm)])
        for path, rows in _table_rows(artifact):
            heading = path.removeprefix("artifact.").replace("_", " ").replace(".", " / ").title()
            story.append(Paragraph(escape(heading), section_style))
            for index, row in enumerate(rows, start=1):
                story.append(Paragraph(f"Record {index}", small_style))
                flat = _flatten_mapping(row)
                record_rows = [
                    [Paragraph(f"<b>{escape(key)}</b>", small_style), Paragraph(_pdf_text(value), small_style)]
                    for key, value in flat.items()
                ] or [[Paragraph("Record", small_style), Paragraph("", small_style)]]
                table = Table(record_rows, colWidths=[64 * mm, 174 * mm])
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F7F6")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#D5E0DD")),
                        ]
                    )
                )
                story.extend([table, Spacer(1, 2 * mm)])

    story.extend(
        [
            Spacer(1, 4 * mm),
            Paragraph("Document integrity", section_style),
            Paragraph(
                f"Artifact SHA-256: {_pdf_text(artifact_sha256)}",
                small_style,
            ),
            Paragraph(
                "Source organizations, proof identifiers and SHA-256 fingerprints remain attached to the governed evidence so the analytical result can be traced back to its published source boundary.",
                small_style,
            ),
        ]
    )

    def page_brand(canvas, doc) -> None:
        draw_pdf_branding(
            canvas,
            doc,
            sample=sample,
            order_id=None if sample else purchase_id,
            jurisdiction=jurisdiction,
            generated_at=artifact.get("captured_at"),
            artifact_sha256=artifact_sha256,
            verification_url=verification_url,
        )

    document.build(story, onFirstPage=page_brand, onLaterPages=page_brand)
    return (
        _filename(product_code, purchase_id, "pdf", sample=sample),
        _PDF_MIME,
        buffer.getvalue(),
    )
