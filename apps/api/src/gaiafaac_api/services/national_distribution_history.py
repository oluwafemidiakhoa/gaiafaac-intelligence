from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import NationalDistribution, ReportingPeriod
from gaiafaac_api.national_distribution_schemas import PublishedNationalDistribution
from gaiafaac_api.services.national_distribution import published_national_distribution


def recent_published_national_distributions(
    session: Session, *, limit: int = 12
) -> list[PublishedNationalDistribution]:
    """Return recent governed national distributions in chronological order."""
    bounded_limit = max(1, min(limit, 24))
    periods = list(
        session.scalars(
            select(ReportingPeriod)
            .join(
                NationalDistribution,
                NationalDistribution.reporting_period_id == ReportingPeriod.id,
            )
            .where(
                ReportingPeriod.is_published.is_(True),
                ReportingPeriod.is_demo.is_(False),
                NationalDistribution.is_published.is_(True),
                NationalDistribution.is_demo.is_(False),
                NationalDistribution.verification_status == VerificationStatus.HUMAN_VERIFIED,
            )
            .order_by(ReportingPeriod.revenue_month.desc())
            .limit(bounded_limit)
        )
    )
    results = [published_national_distribution(session, period) for period in periods]
    return [result for result in reversed(results) if result is not None]
