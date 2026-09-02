import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ReportedUnit, UserRole, VerificationStatus
from gaiafaac_api.database.models import (
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    User,
)
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.errors import ApprovalError, ImportContractError
from gaiafaac_api.pipeline.national_distribution import (
    NationalDistributionImportRequest,
    approve_national_distribution,
    import_national_distribution,
    publish_national_distribution,
)
from gaiafaac_api.pipeline.national_scope import declare_national_states_scope
from gaiafaac_api.services.national_distribution import published_national_distribution
from gaiafaac_api.services.national_distribution_history import (
    recent_published_national_distributions,
)


def _user(session: Session, role: UserRole) -> User:
    user = User(
        email=f"{uuid.uuid4()}@example.test",
        full_name=role.value.title(),
        role=role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    return user


def _period_with_jurisdictions(session: Session) -> ReportingPeriod:
    seed_states(session)
    period = ReportingPeriod(
        revenue_month=date(2026, 6, 1),
        reporting_label="June 2026 governed state allocations",
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    source = SourceDocument(
        reporting_period_id=period.id,
        source_organization="OAGF",
        original_filename="state-table.pdf",
        storage_path="state-table.pdf",
        sha256="a" * 64,
        mime_type="application/pdf",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    states = list(session.scalars(select(State).order_by(State.name)))
    for index, state in enumerate(states):
        session.add(
            StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=source.id,
                net_allocation=(Decimal("838208000000.00") if index == 0 else Decimal("0.00")),
                net_allocation_original=("838208000000.00" if index == 0 else "0.00"),
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                is_demo=False,
                is_published=True,
            )
        )
    session.commit()
    return period


def _national_source(tmp_path: Path, name: str = "national-communique.txt") -> Path:
    path = tmp_path / name
    path.write_text("official national distribution evidence", encoding="utf-8")
    return path


def _import_national(
    session: Session,
    tmp_path: Path,
    period: ReportingPeriod,
    *,
    net: str = "2551",
    derivation_treatment: str = "separate",
    source_type: str = "canonical_national_evidence",
    source_authority: str = "canonical",
    canonical_source_status: str = "available",
):
    return import_national_distribution(
        session,
        NationalDistributionImportRequest(
            path=_national_source(tmp_path),
            reporting_period_id=period.id,
            source_organization="Federal Ministry of Finance",
            reported_unit="billion_naira",
            net_distributable_amount=net,
            federal_amount="923.438",
            states_amount="838.208",
            local_governments_amount="591.390",
            derivation_amount=("197.610" if derivation_treatment != "not_reported" else None),
            derivation_treatment=derivation_treatment,
            publication_date=date(2026, 7, 1),
            source_url="https://example.test/official-communique",
            source_type=source_type,
            source_authority=source_authority,
            canonical_source_status=canonical_source_status,
        ),
    )


def _declare_scope(session: Session, run_id: str) -> None:
    declare_national_states_scope(
        session,
        run_id=uuid.UUID(run_id),
        states_scope="states_plus_fct_37",
    )


def test_rounded_headline_reconciles_using_source_precision(
    session: Session, tmp_path: Path
) -> None:
    period = _period_with_jurisdictions(session)
    result = _import_national(session, tmp_path, period)

    assert result.blocking_finding_count == 0
    _declare_scope(session, result.run_id)
    reviewer = _user(session, UserRole.REVIEWER)
    publisher = _user(session, UserRole.ADMINISTRATOR)
    approve_national_distribution(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)
    publish_national_distribution(
        session, run_id=uuid.UUID(result.run_id), reviewer_id=publisher.id
    )

    published = published_national_distribution(session, period)
    assert published is not None
    assert published.net_distributable_amount.value == "2551000000000.00"
    assert published.component_reconciliation.status == "reconciled"
    assert published.component_reconciliation.variance == "-354000000.00"
    assert published.component_reconciliation.tolerance == "500000000.00"
    assert published.jurisdiction_reconciliation.status == "reconciled"
    assert published.jurisdiction_reconciliation.derived_total == "838208000000.00"
    assert published.source.sha256
    assert published.source.source_organization == "Federal Ministry of Finance"
    assert published.source.source_type == "canonical_national_evidence"
    assert published.source.source_authority == "canonical"
    assert published.canonical_source_status == "available"


def test_material_component_mismatch_blocks_human_approval(
    session: Session, tmp_path: Path
) -> None:
    period = _period_with_jurisdictions(session)
    result = _import_national(session, tmp_path, period, net="2500")
    assert result.blocking_finding_count == 1
    _declare_scope(session, result.run_id)
    reviewer = _user(session, UserRole.REVIEWER)
    with pytest.raises(ApprovalError, match="blocking validation"):
        approve_national_distribution(
            session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id
        )


def test_unknown_derivation_semantics_stays_explicitly_unavailable(
    session: Session, tmp_path: Path
) -> None:
    period = _period_with_jurisdictions(session)
    result = _import_national(
        session,
        tmp_path,
        period,
        derivation_treatment="not_reported",
    )
    assert result.blocking_finding_count == 0
    _declare_scope(session, result.run_id)
    reviewer = _user(session, UserRole.REVIEWER)
    publisher = _user(session, UserRole.ADMINISTRATOR)
    approve_national_distribution(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)
    publish_national_distribution(
        session, run_id=uuid.UUID(result.run_id), reviewer_id=publisher.id
    )
    published = published_national_distribution(session, period)
    assert published is not None
    assert published.component_reconciliation.status == "unavailable"
    assert published.derivation_treatment == "not_reported"
    assert published.jurisdiction_reconciliation.status == "reconciled"


def test_four_eyes_blocks_same_administrator_from_review_and_publish(
    session: Session, tmp_path: Path
) -> None:
    period = _period_with_jurisdictions(session)
    result = _import_national(session, tmp_path, period)
    _declare_scope(session, result.run_id)
    administrator = _user(session, UserRole.ADMINISTRATOR)
    approve_national_distribution(
        session,
        run_id=uuid.UUID(result.run_id),
        reviewer_id=administrator.id,
    )
    with pytest.raises(ApprovalError, match="reviewer cannot publish"):
        publish_national_distribution(
            session,
            run_id=uuid.UUID(result.run_id),
            reviewer_id=administrator.id,
        )


def test_unknown_states_scope_allows_partial_national_evidence(
    session: Session, tmp_path: Path
) -> None:
    period = _period_with_jurisdictions(session)
    result = _import_national(session, tmp_path, period)
    assert result.blocking_finding_count == 0

    reviewer = _user(session, UserRole.REVIEWER)
    publisher = _user(session, UserRole.ADMINISTRATOR)
    approve_national_distribution(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)
    publish_national_distribution(
        session, run_id=uuid.UUID(result.run_id), reviewer_id=publisher.id
    )

    published = published_national_distribution(session, period)
    assert published is not None
    assert published.states_scope == "not_declared"
    assert published.component_reconciliation.status == "reconciled"
    assert published.jurisdiction_reconciliation.status == "unavailable"
    assert "does not establish" in published.jurisdiction_reconciliation.note


def test_official_secondary_evidence_never_claims_canonical_source(
    session: Session, tmp_path: Path
) -> None:
    period = _period_with_jurisdictions(session)
    result = _import_national(
        session,
        tmp_path,
        period,
        source_type="official_government_press_release",
        source_authority="official_secondary",
        canonical_source_status="missing",
    )
    reviewer = _user(session, UserRole.REVIEWER)
    publisher = _user(session, UserRole.ADMINISTRATOR)
    approve_national_distribution(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)
    publish_national_distribution(
        session, run_id=uuid.UUID(result.run_id), reviewer_id=publisher.id
    )

    published = published_national_distribution(session, period)
    assert published is not None
    assert published.source.source_type == "official_government_press_release"
    assert published.source.source_authority == "official_secondary"
    assert published.canonical_source_status == "missing"
    assert published.component_reconciliation.status == "reconciled"
    assert published.jurisdiction_reconciliation.status == "unavailable"


def test_noncanonical_evidence_cannot_claim_canonical_source_available(
    session: Session, tmp_path: Path
) -> None:
    period = _period_with_jurisdictions(session)
    with pytest.raises(ImportContractError, match="cannot claim"):
        _import_national(
            session,
            tmp_path,
            period,
            source_type="official_government_press_release",
            source_authority="official_secondary",
            canonical_source_status="available",
        )


def test_history_lists_a_period_once_even_with_two_published_sources(
    session: Session, tmp_path: Path
) -> None:
    """A period can legitimately have more than one published NationalDistribution -
    e.g. an independently corroborating or corrected release under a new source
    document (uq_national_distribution_source is keyed on source, not period alone).
    The history trend list must still show that period exactly once."""
    period = _period_with_jurisdictions(session)

    first = _import_national(session, tmp_path, period)
    _declare_scope(session, first.run_id)
    approve_national_distribution(
        session, run_id=uuid.UUID(first.run_id), reviewer_id=_user(session, UserRole.REVIEWER).id
    )
    publish_national_distribution(
        session,
        run_id=uuid.UUID(first.run_id),
        reviewer_id=_user(session, UserRole.ADMINISTRATOR).id,
    )

    second_source = tmp_path / "second-communique.txt"
    second_source.write_text("independently corroborating national evidence", encoding="utf-8")
    second = import_national_distribution(
        session,
        NationalDistributionImportRequest(
            path=second_source,
            reporting_period_id=period.id,
            source_organization="Federal Ministry of Finance (corroborating release)",
            reported_unit="billion_naira",
            net_distributable_amount="2551",
            federal_amount="923.438",
            states_amount="838.208",
            local_governments_amount="591.390",
            derivation_amount="197.610",
            derivation_treatment="separate",
            publication_date=date(2026, 7, 2),
            source_url="https://example.test/second-official-communique",
            source_type="canonical_national_evidence",
            source_authority="canonical",
            canonical_source_status="available",
        ),
    )
    _declare_scope(session, second.run_id)
    approve_national_distribution(
        session, run_id=uuid.UUID(second.run_id), reviewer_id=_user(session, UserRole.REVIEWER).id
    )
    publish_national_distribution(
        session,
        run_id=uuid.UUID(second.run_id),
        reviewer_id=_user(session, UserRole.ADMINISTRATOR).id,
    )

    history = recent_published_national_distributions(session, limit=24)
    matching = [item for item in history if item.reporting_period_id == str(period.id)]
    assert len(matching) == 1
