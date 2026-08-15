from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import Numeric, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import ReportingPeriod

EXPECTED_TABLES = {
    "api_keys",
    "api_requests",
    "audit_logs",
    "claim_revisions",
    "customer_sessions",
    "evidence_conflict_claims",
    "evidence_conflicts",
    "evidence_manifests",
    "evidence_sources",
    "evidence_verifications",
    "extraction_runs",
    "fiscal_certificates",
    "fiscal_claims",
    "fiscal_events",
    "fiscal_proofs",
    "fiscal_states",
    "forecasts",
    "generated_insights",
    "national_distributions",
    "organization_invites",
    "organization_memberships",
    "organizations",
    "pilot_leads",
    "reporting_periods",
    "source_documents",
    "state_allocation_components",
    "state_allocations",
    "state_igr_records",
    "state_indicators",
    "states",
    "subscriptions",
    "users",
    "validation_results",
}


def test_metadata_defines_all_current_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_money_columns_are_fixed_precision() -> None:
    allocation = Base.metadata.tables["state_allocations"]
    for name in ("gross_total", "total_deductions", "net_allocation"):
        column_type = allocation.c[name].type
        assert isinstance(column_type, Numeric)
        assert (column_type.precision, column_type.scale) == (24, 2)
    assert Decimal("0.10") + Decimal("0.20") == Decimal("0.30")

    component = Base.metadata.tables["state_allocation_components"]
    assert {"gross_amount", "deduction_amount", "net_amount"} <= set(component.c.keys())


def test_database_rejects_published_demo_period(session: Session) -> None:
    session.add(
        ReportingPeriod(
            revenue_month=date(2099, 1, 1),
            reporting_label="DEMO DATA",
            verification_status=VerificationStatus.PENDING,
            is_demo=True,
            is_published=True,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_source_document_has_lineage_constraints(session: Session) -> None:
    columns = {column["name"] for column in inspect(session.bind).get_columns("source_documents")}
    assert {"sha256", "storage_path", "source_url", "document_version"} <= columns
