from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod
from gaiafaac_api.pipeline.collection.oagf_urls import candidate_urls
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest, ImportResult

logger = logging.getLogger(__name__)

OAGF_ORG = "Office of the Accountant-General of the Federation (OAGF)"
Downloader = Callable[[str], Path | None]
Importer = Callable[[Session, ImportRequest], ImportResult]


@dataclass(frozen=True)
class QueuedMonth:
    run_id: str
    revenue_month: date
    reporting_label: str
    records_extracted: int
    blocking_finding_count: int


@dataclass(frozen=True)
class CollectionSummary:
    checked: list[date]
    queued: list[QueuedMonth]
    skipped: list[date]
    errors: list[tuple[date, str]]


def _reporting_label(revenue: date) -> str:
    return (
        f"OAGF FAAC Disbursement — {revenue.strftime('%B %Y')} "
        "(Table III: state distribution)"
    )


def _add_months(anchor: date, delta: int) -> date:
    index = (anchor.year * 12 + (anchor.month - 1)) + delta
    return date(index // 12, index % 12 + 1, 1)


def _already_ingested(session: Session, revenue: date) -> bool:
    return (
        session.scalar(
            select(ReportingPeriod).where(
                ReportingPeriod.revenue_month == revenue,
                ReportingPeriod.is_demo.is_(False),
            )
        )
        is not None
    )


def run_collection(
    session: Session,
    *,
    months_back: int = 3,
    downloader: Downloader,
    importer: Importer = import_file,
    now: date | None = None,
) -> CollectionSummary:
    """Fetch, import, and queue any newly published OAGF months. Never publishes."""
    anchor = now or date.today()
    checked: list[date] = []
    queued: list[QueuedMonth] = []
    skipped: list[date] = []
    errors: list[tuple[date, str]] = []

    for step in range(1, months_back + 1):
        revenue = _add_months(anchor.replace(day=1), -step)
        checked.append(revenue)
        if _already_ingested(session, revenue):
            skipped.append(revenue)
            continue

        path: Path | None = None
        source_url: str | None = None
        failed = False
        for url in candidate_urls(revenue.year, revenue.month):
            try:
                path = downloader(url)
            except Exception as error:  # noqa: BLE001 - one bad month must not abort the run
                errors.append((revenue, f"download failed: {error}"))
                failed = True
                break
            if path is not None:
                source_url = url
                break
        if failed:
            continue
        if path is None:
            skipped.append(revenue)
            continue

        try:
            result = importer(
                session,
                ImportRequest(
                    path=path,
                    source_organization=OAGF_ORG,
                    revenue_month=revenue,
                    reporting_label=_reporting_label(revenue),
                    source_url=source_url,
                    reported_unit="naira",
                ),
            )
        except Exception as error:  # noqa: BLE001 - surface, don't abort the whole run
            errors.append((revenue, f"import failed: {error}"))
            continue

        queued.append(
            QueuedMonth(
                run_id=result.run_id,
                revenue_month=revenue,
                reporting_label=_reporting_label(revenue),
                records_extracted=result.records_extracted,
                blocking_finding_count=result.blocking_finding_count,
            )
        )
        logger.info("Queued %s (run=%s) for review", _reporting_label(revenue), result.run_id)

    return CollectionSummary(checked, queued, skipped, errors)
