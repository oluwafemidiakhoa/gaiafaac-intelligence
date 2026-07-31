import csv
from datetime import date

from fastapi.testclient import TestClient

from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest


def test_pending_endpoint_returns_queued_month(session, tmp_path):
    seed_states(session)
    csv_path = tmp_path / "jan.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["state", "gross_total", "total_deductions", "net_allocation", "reported_unit"]
        )
        writer.writerow(["Lagos", "1000.00", "100.00", "900.00", "naira"])
    import_file(
        session,
        ImportRequest(
            path=csv_path,
            source_organization="OAGF",
            revenue_month=date(2024, 1, 1),
            reporting_label="OAGF Jan 2024",
            reported_unit="naira",
        ),
    )

    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/review/pending")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["reporting_label"] == "OAGF Jan 2024"
    assert body[0]["expected_states"] == 37
    assert "900" not in response.text  # no figures
