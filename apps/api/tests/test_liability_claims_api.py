from datetime import UTC, datetime
from decimal import Decimal

from gaiafaac_api.api.v1.routes.fiscal_claims import jurisdiction_fiscal_claims
from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.fiscal_trust import record_evidence_conflict


def _state(session) -> State:
    state = State(
        name="Kebbi",
        code="KE",
        slug="kebbi",
        geopolitical_zone="North West",
        capital="Birnin Kebbi",
        is_fct=False,
    )
    session.add(state)
    session.flush()
    return state


def _source(session, *, sha: str, supersedes=None) -> SourceDocument:
    source = SourceDocument(
        source_organization="Kebbi State Government",
        source_url=f"https://kebbistate.gov.ng/liabilities-{sha[0]}.pdf",
        original_filename=f"liabilities-{sha[0]}.pdf",
        storage_path=f"/tmp/liabilities-{sha[0]}.pdf",
        sha256=sha,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.COMPLETED,
        source_status=SourceStatus.APPROVED,
        supersedes_document_id=supersedes,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def _publish(
    session,
    *,
    state: State,
    source: SourceDocument,
    metric: str,
    value: Decimal | None,
    value_text: str,
):
    return publish_domain_claim(
        session,
        domain="liabilities",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2024",
        metric=metric,
        value=value,
        value_text=value_text,
        unit="currency",
        currency="NGN",
        effective_at=datetime(2024, 12, 31, 23, 59, tzinfo=UTC),
        published_at=datetime(2026, 8, 22, 20, 0, tzinfo=UTC),
        source_page=10,
        source_table="Domestic arrears summary",
        extraction_method="test_liability_source",
        human_reviewed=True,
        reconciled=True,
    )


def test_liability_claim_api_preserves_dash_revision_and_current_view(session):
    state = _state(session)
    first_source = _source(session, sha="a" * 64)
    first = _publish(
        session,
        state=state,
        source=first_source,
        metric="salary_arrears",
        value=None,
        value_text="-",
    )
    second_source = _source(session, sha="b" * 64, supersedes=first_source.id)
    second = _publish(
        session,
        state=state,
        source=second_source,
        metric="salary_arrears",
        value=None,
        value_text="-",
    )
    session.commit()

    current = jurisdiction_fiscal_claims(
        "NG-KE", session, "liabilities", "2024", "salary_arrears", False, 100
    )
    history = jurisdiction_fiscal_claims(
        "NG-KE", session, "liabilities", "2024", "salary_arrears", True, 100
    )

    assert first.gaia_id != second.gaia_id
    assert len(current.data) == 1
    assert current.data[0].gaia_id == second.gaia_id
    assert current.data[0].value == "-"
    assert current.data[0].supersedes_gaia_id == first.gaia_id
    assert len(history.data) == 2
    original = next(item for item in history.data if item.gaia_id == first.gaia_id)
    assert original.superseded_by_gaia_id == second.gaia_id
    assert all(item.object_type == "liabilities" for item in history.data)
    assert all(item.source.document_sha256 in {"a" * 64, "b" * 64} for item in history.data)


def test_liability_numeric_revision_and_conflict_remain_auditable(session):
    state = _state(session)
    first_source = _source(session, sha="c" * 64)
    first = _publish(
        session,
        state=state,
        source=first_source,
        metric="contractor_arrears",
        value=Decimal("100.00"),
        value_text="100.00",
    )
    second_source = _source(session, sha="d" * 64, supersedes=first_source.id)
    second = _publish(
        session,
        state=state,
        source=second_source,
        metric="contractor_arrears",
        value=Decimal("120.00"),
        value_text="120.00",
    )
    conflict = record_evidence_conflict(
        session,
        claim_gaia_ids=[first.gaia_id, second.gaia_id],
        explanation="Two retained official liability publications report different values.",
        detected_at=datetime(2026, 8, 22, 20, 5, tzinfo=UTC),
    )
    session.commit()

    history = jurisdiction_fiscal_claims(
        "KE", session, "liabilities", "2024", "contractor_arrears", True, 100
    )

    assert len(history.data) == 2
    assert {item.value for item in history.data} == {"100.00", "120.00"}
    assert conflict.object_type == "liabilities"
    assert conflict.metric == "contractor_arrears"
    assert conflict.fiscal_period == "2024"
    assert conflict.status.value == "unresolved"
