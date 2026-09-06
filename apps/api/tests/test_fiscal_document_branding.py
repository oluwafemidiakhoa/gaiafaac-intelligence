from __future__ import annotations

import io

from openpyxl import load_workbook

from gaiafaac_api.services.branded_one_time_exports import (
    build_one_time_excel,
    build_one_time_pdf,
)
from gaiafaac_api.services.document_branding import BRAND_NAME, SAMPLE_NOTICE, SAMPLE_WATERMARK


def _artifact() -> dict:
    return {
        "schema": "gaia-one-time-historical-export-v1",
        "captured_at": "2026-09-06T13:00:00+00:00",
        "request": {
            "state_slug": "lagos",
            "state_code": "LA",
            "domain": "igr",
            "start_year": 2023,
            "end_year": 2024,
        },
        "rows": [
            {
                "domain": "igr",
                "state_name": "Lagos",
                "state_code": "LA",
                "period": "2024",
                "value": "1261556415048.56",
                "unit": "NGN",
                "source_organization": "National Bureau of Statistics",
                "source_url": "https://example.gov.ng/nbs-igr.xlsx",
                "source_sha256": "a" * 64,
                "verification_status": "human_verified",
            }
        ],
    }


def test_paid_excel_uses_gaia_fiscal_intelligence_brand_on_every_sheet():
    filename, media_type, body = build_one_time_excel(
        purchase_id="12345678-1234-5678-1234-567812345678",
        product_code="historical_evidence_export",
        amount_naira="75000",
        currency="NGN",
        completed_at="2026-09-06T13:30:00+00:00",
        artifact=_artifact(),
        jurisdiction="Lagos",
    )

    assert filename.startswith("gaia-fiscal-intelligence-")
    assert media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    workbook = load_workbook(io.BytesIO(body), data_only=True)
    assert workbook["Summary"]["A1"].value == BRAND_NAME
    for sheet in workbook.worksheets:
        assert sheet.oddHeader.center.text == BRAND_NAME
        assert BRAND_NAME in (sheet.oddFooter.left.text or "")


def test_sample_excel_is_visibly_and_print_watermarked():
    filename, _media_type, body = build_one_time_excel(
        purchase_id="SAMPLE-lagos-2026",
        product_code="decision_pack",
        amount_naira="50000",
        currency="NGN",
        completed_at="Not applicable — demonstration sample",
        artifact=_artifact(),
        sample=True,
        jurisdiction="Lagos",
    )

    assert filename == "gaia-fiscal-intelligence-sample-decision-pack.xlsx"
    workbook = load_workbook(io.BytesIO(body), data_only=True)
    assert workbook["Summary"]["A3"].value == SAMPLE_NOTICE
    for sheet in workbook.worksheets:
        assert sheet.oddHeader.center.text == SAMPLE_WATERMARK


def test_paid_and_sample_pdf_are_real_branded_documents():
    paid_filename, paid_media_type, paid_body = build_one_time_pdf(
        purchase_id="12345678-1234-5678-1234-567812345678",
        product_code="decision_pack",
        amount_naira="50000",
        currency="NGN",
        completed_at="2026-09-06T13:30:00+00:00",
        artifact=_artifact(),
        jurisdiction="Lagos",
    )
    sample_filename, sample_media_type, sample_body = build_one_time_pdf(
        purchase_id="SAMPLE-lagos-2026",
        product_code="decision_pack",
        amount_naira="50000",
        currency="NGN",
        completed_at="Not applicable — demonstration sample",
        artifact=_artifact(),
        sample=True,
        jurisdiction="Lagos",
    )

    assert paid_filename.startswith("gaia-fiscal-intelligence-decision-pack-")
    assert sample_filename == "gaia-fiscal-intelligence-sample-decision-pack.pdf"
    assert paid_media_type == sample_media_type == "application/pdf"
    assert paid_body.startswith(b"%PDF-")
    assert sample_body.startswith(b"%PDF-")
    assert len(paid_body) > 1000
    assert len(sample_body) > 1000
