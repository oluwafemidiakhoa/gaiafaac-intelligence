from __future__ import annotations

import io
import zipfile

from gaiafaac_api.services.institutional_one_time_exports import build_one_time_excel


def _artifact() -> dict:
    months = []
    for index, (gross, deductions, net) in enumerate(
        [
            (100_000_000_000, 20_000_000_000, 80_000_000_000),
            (120_000_000_000, 24_000_000_000, 96_000_000_000),
            (90_000_000_000, 22_500_000_000, 67_500_000_000),
        ],
        start=1,
    ):
        months.append(
            {
                "revenue_month": f"2026-0{index}-01",
                "reporting_label": f"Month {index}",
                "gross_total": str(gross),
                "total_deductions": str(deductions),
                "net_allocation": str(net),
                "reconciliation_status": "reconciled",
                "proof_id": f"GF1-NG-LA-20260{index}-TEST",
                "proof_path": f"/fiscal-proof/lagos/2026-0{index}-01",
                "source_organization": "OAGF",
                "source_sha256": str(index) * 64,
                "human_verified": True,
            }
        )

    return {
        "schema": "gaia-sample-decision-pack-v1",
        "captured_at": "2026-09-07T05:00:00+00:00",
        "request": {"state_slug": "lagos", "year": 2026, "sample": True},
        "decision_packet": {
            "packet_version": "2",
            "state_name": "Lagos",
            "state_slug": "lagos",
            "state_code": "LA",
            "geopolitical_zone": "South West",
            "year": 2026,
            "coverage_label": "Partial 2026 series · 3 of 12 months published",
            "months_published": 3,
            "annual_gross": "310000000000",
            "annual_deductions": "66500000000",
            "annual_net": "243500000000",
            "deduction_burden_pct": 21.45,
            "net_retention_pct": 78.55,
            "momentum": "Weakening",
            "momentum_pct": -15.63,
            "volatility": "Moderate",
            "volatility_cv_pct": 14.2,
            "evidence_status": "Verified",
            "igr_records": [],
            "igr_note": "No published, human-verified IGR evidence is available.",
            "watch_events": [],
            "months": months,
            "disclaimer": "Evidence dossier only.",
        },
        "statement": "SAMPLE",
    }


def test_decision_pack_charts_reference_visible_analytics_table():
    _filename, _media_type, body = build_one_time_excel(
        purchase_id="SAMPLE-lagos-2026",
        product_code="decision_pack",
        amount_naira="50000",
        currency="NGN",
        completed_at="Not applicable",
        artifact=_artifact(),
        sample=True,
        jurisdiction="Lagos",
    )

    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        chart_xml = "\n".join(
            archive.read(name).decode("utf-8")
            for name in archive.namelist()
            if name.startswith("xl/charts/chart") and name.endswith(".xml")
        )

    assert "Fiscal Analytics!$A$" in chart_xml
    assert "Fiscal Analytics!$B$" in chart_xml
    assert "Fiscal Analytics!$D$" in chart_xml
    assert "Fiscal Analytics!$E$" in chart_xml
    assert "Fiscal Analytics!$X$" not in chart_xml
    assert "Fiscal Analytics!$Y$" not in chart_xml
    assert "Fiscal Analytics!$Z$" not in chart_xml
    assert "Fiscal Analytics!$AA$" not in chart_xml
