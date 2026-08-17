from datetime import date
from decimal import Decimal

from gaiafaac_api.database.enums import (
    ExtractionStatus,
    ReportedUnit,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    ExtractionRun,
    NationalDistribution,
    ReportingPeriod,
    SourceDocument,
)
from gaiafaac_api.services.national_distribution import published_national_distribution


def _published_period(session, *, explicit_months: bool) -> ReportingPeriod:
    period = ReportingPeriod(
        revenue_month=date(2026, 6, 1),
        disbursement_month=date(2026, 6, 1) if explicit_months else None,
        allocation_period_month=date(2026, 5, 1) if explicit_months else None,
        reporting_label="June 2026 governed state allocations",
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()

    source = SourceDocument(
        reporting_period_id=period.id,
        source_organization="Federal Ministry of Information",
        original_filename="national.html",
        storage_path="national.html",
        sha256=("b" if explicit_months else "c") * 64,
        mime_type="text/html",
        is_demo=False,
    )
    session.add(source)
    session.flush()

    distribution = NationalDistribution(
        reporting_period_id=period.id,
        source_document_id=source.id,
        net_distributable_amount=Decimal("2300000000000.00"),
        federal_amount=Decimal("818680000000.00"),
        states_amount=Decimal("759141000000.00"),
        local_governments_amount=Decimal("534277000000.00"),
        derivation_amount=Decimal("188132000000.00"),
        reported_unit=ReportedUnit.NAIRA,
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        is_demo=False,
        is_published=True,
    )
    session.add(distribution)
    session.flush()

    session.add(
        ExtractionRun(
            source_document_id=source.id,
            status=ExtractionStatus.COMPLETED,
            extractor_name="controlled_national_distribution",
            extractor_version="2",
            records_extracted=1,
            configuration={
                "scope": "national_distribution",
                "distribution_id": str(distribution.id),
                "derivation_treatment": "separate",
                "source_type": "official_government_press_release",
                "source_authority": "official_secondary",
                "canonical_source_status": "missing",
                "original_values": {
                    "net_distributable_amount": "2300",
                    "federal_amount": "818.680",
                    "states_amount": "759.141",
                    "local_governments_amount": "534.277",
                    "derivation_amount": "188.132",
                },
            },
        )
    )
    session.commit()
    return period


def test_published_national_distribution_exposes_both_month_semantics(session) -> None:
    period = _published_period(session, explicit_months=True)

    published = published_national_distribution(session, period)

    assert published is not None
    assert published.revenue_month == date(2026, 6, 1)
    assert published.disbursement_month == date(2026, 6, 1)
    assert published.allocation_period_month == date(2026, 5, 1)


def test_legacy_period_falls_back_only_for_disbursement_month(session) -> None:
    period = _published_period(session, explicit_months=False)

    published = published_national_distribution(session, period)

    assert published is not None
    assert published.disbursement_month == date(2026, 6, 1)
    assert published.allocation_period_month is None
