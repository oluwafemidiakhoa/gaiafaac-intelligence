from datetime import date

from sqlalchemy import select

from gaiafaac_api.database.models import ReportingPeriod
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.collection import collector as collector_module
from gaiafaac_api.pipeline.collection.collector import QueuedMonth, run_collection
from gaiafaac_api.pipeline.importer import ImportResult


def _fake_importer_factory(session):
    """Importer stub that records a real (non-demo) requires_review period."""

    def _fake_importer(sess, request):
        period = ReportingPeriod(
            revenue_month=request.revenue_month,
            reporting_label=request.reporting_label,
            is_demo=False,
            is_published=False,
        )
        sess.add(period)
        sess.flush()
        return ImportResult(
            run_id=str(period.id),
            reporting_period_id=str(period.id),
            source_document_id=str(period.id),
            records_extracted=36,
            finding_count=2,
            blocking_finding_count=2,
        )

    return _fake_importer


def test_collects_available_month_and_never_publishes(session, tmp_path):
    seed_states(session)
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.7 x")

    summary = run_collection(
        session,
        months_back=1,
        downloader=lambda _url: pdf,
        importer=_fake_importer_factory(session),
        now=date(2024, 2, 15),
    )

    assert summary.queued == [
        QueuedMonth(
            run_id=summary.queued[0].run_id,
            revenue_month=date(2024, 1, 1),
            reporting_label=summary.queued[0].reporting_label,
            records_extracted=36,
            blocking_finding_count=2,
        )
    ]
    # nothing is ever published
    assert (
        session.scalars(
            select(ReportingPeriod).where(ReportingPeriod.is_published.is_(True))
        ).all()
        == []
    )


def test_is_idempotent(session, tmp_path):
    seed_states(session)
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.7 x")
    kwargs = dict(
        months_back=1,
        downloader=lambda _url: pdf,
        importer=_fake_importer_factory(session),
        now=date(2024, 2, 15),
    )
    run_collection(session, **kwargs)
    second = run_collection(session, **kwargs)
    assert second.queued == []
    assert second.skipped == [date(2024, 1, 1)]


def test_missing_month_is_skipped(session, tmp_path):
    seed_states(session)
    summary = run_collection(
        session,
        months_back=1,
        downloader=lambda _url: None,  # 404 everywhere
        importer=_fake_importer_factory(session),
        now=date(2024, 2, 15),
    )
    assert summary.queued == []
    assert summary.skipped == [date(2024, 1, 1)]


def test_collector_cannot_publish():
    from pathlib import Path

    source = Path(collector_module.__file__).read_text(encoding="utf-8")
    assert "publish_import" not in source
    assert "approve_import" not in source
