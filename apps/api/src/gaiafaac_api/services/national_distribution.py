from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import (
    ExtractionRun,
    NationalDistribution,
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
)
from gaiafaac_api.national_distribution_schemas import (
    NationalObservedValue,
    NationalReconciliation,
    NationalSource,
    PublishedNationalDistribution,
)
from gaiafaac_api.pipeline.national_distribution import reconciliation_for_distribution

EXPECTED_JURISDICTIONS = 37


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _observed(value: Decimal | None) -> NationalObservedValue:
    return NationalObservedValue(
        value=_money(value),
        evidence_class="observed" if value is not None else "missing",
    )


def _run_for_distribution(
    session: Session, distribution: NationalDistribution
) -> ExtractionRun | None:
    runs = session.scalars(
        select(ExtractionRun)
        .where(ExtractionRun.source_document_id == distribution.source_document_id)
        .order_by(ExtractionRun.created_at.desc())
    )
    for run in runs:
        configuration = run.configuration or {}
        if (
            configuration.get("scope") == "national_distribution"
            and str(configuration.get("distribution_id")) == str(distribution.id)
        ):
            return run
    return None


def _config(run: ExtractionRun) -> tuple[str, str, dict[str, str | None]]:
    configuration = run.configuration or {}
    treatment = str(configuration.get("derivation_treatment") or "not_reported")
    scope = str(configuration.get("states_scope") or "not_declared")
    originals = configuration.get("original_values") or {}
    if not isinstance(originals, dict):
        originals = {}
    return treatment, scope, {
        str(key): None if value is None else str(value)
        for key, value in originals.items()
    }


def _decimal_places(original: str | None) -> int | None:
    if original is None:
        return None
    cleaned = str(original).strip().replace(",", "").replace("₦", "")
    if cleaned.casefold().startswith("ngn"):
        cleaned = cleaned[3:].strip()
    if cleaned.casefold().endswith("ngn"):
        cleaned = cleaned[:-3].strip()
    if "." not in cleaned:
        return 0 if cleaned.lstrip("+-").isdigit() else None
    whole, fractional = cleaned.rsplit(".", 1)
    if not whole.lstrip("+-").isdigit() or not fractional.isdigit():
        return None
    return len(fractional)


def _states_tolerance(
    distribution: NationalDistribution, originals: dict[str, str | None]
) -> Decimal:
    places = _decimal_places(originals.get("states_amount"))
    if places is None:
        return Decimal("0.01")
    multipliers = {
        "naira": Decimal("1"),
        "thousand_naira": Decimal("1000"),
        "million_naira": Decimal("1000000"),
        "billion_naira": Decimal("1000000000"),
    }
    quantum = multipliers.get(
        distribution.reported_unit.value, Decimal("0.01")
    ) / (Decimal(10) ** places)
    return max(Decimal("0.01"), quantum / Decimal("2"))


def _jurisdiction_reconciliation(
    session: Session,
    distribution: NationalDistribution,
    *,
    states_scope: str,
    originals: dict[str, str | None],
) -> tuple[NationalReconciliation, int]:
    rows = list(
        session.execute(
            select(StateAllocation, State)
            .join(State, StateAllocation.state_id == State.id)
            .where(
                StateAllocation.reporting_period_id == distribution.reporting_period_id,
                StateAllocation.is_published.is_(True),
                StateAllocation.is_demo.is_(False),
            )
        ).tuples()
    )
    covered = len(rows)
    expected = 36 if states_scope == "states_only_36" else EXPECTED_JURISDICTIONS
    selected = [
        allocation
        for allocation, state in rows
        if states_scope == "states_plus_fct_37" or not state.is_fct
    ]
    if states_scope not in {"states_only_36", "states_plus_fct_37"}:
        return (
            NationalReconciliation(
                status="unavailable",
                observed_total=_money(distribution.states_amount),
                derived_total=None,
                variance=None,
                tolerance=None,
                evidence_class="missing",
                basis="National states aggregate vs jurisdiction ledger",
                note=(
                    "The national source has no declared states scope. GaiaFAAC will not "
                    "guess whether the reported states amount includes the FCT."
                ),
            ),
            covered,
        )
    basis = (
        "36 states excluding FCT"
        if states_scope == "states_only_36"
        else "36 states plus FCT"
    )
    if len(selected) != expected or any(row.net_allocation is None for row in selected):
        return (
            NationalReconciliation(
                status="incomplete",
                observed_total=_money(distribution.states_amount),
                derived_total=None,
                variance=None,
                tolerance=None,
                evidence_class="missing",
                basis=basis,
                note=(
                    f"Jurisdiction reconciliation requires {expected}/{expected} published "
                    "net allocations on the declared basis."
                ),
            ),
            covered,
        )
    if distribution.states_amount is None:
        return (
            NationalReconciliation(
                status="unavailable",
                observed_total=None,
                derived_total=None,
                variance=None,
                tolerance=None,
                evidence_class="missing",
                basis=basis,
                note="The national source does not contain a states aggregate.",
            ),
            covered,
        )
    ledger_total = sum(
        (row.net_allocation for row in selected if row.net_allocation is not None),
        Decimal("0"),
    )
    tolerance = _states_tolerance(distribution, originals)
    variance = ledger_total - distribution.states_amount
    status = "reconciled" if abs(variance) <= tolerance else "conflicted"
    return (
        NationalReconciliation(
            status=status,
            observed_total=_money(distribution.states_amount),
            derived_total=_money(ledger_total),
            variance=_money(variance),
            tolerance=_money(tolerance),
            evidence_class="derived" if status == "reconciled" else "conflicted",
            basis=basis,
            note=(
                "The official states aggregate reconciles with the published jurisdiction "
                "ledger within source-derived reporting precision."
                if status == "reconciled"
                else "The official states aggregate conflicts with the published jurisdiction ledger."
            ),
        ),
        covered,
    )


def _published_distribution_for_period(
    session: Session, period: ReportingPeriod
) -> NationalDistribution | None:
    return session.scalar(
        select(NationalDistribution)
        .where(
            NationalDistribution.reporting_period_id == period.id,
            NationalDistribution.is_published.is_(True),
            NationalDistribution.is_demo.is_(False),
            NationalDistribution.verification_status == VerificationStatus.HUMAN_VERIFIED,
        )
        .order_by(NationalDistribution.published_at.desc())
        .limit(1)
    )


def published_national_distribution(
    session: Session, period: ReportingPeriod
) -> PublishedNationalDistribution | None:
    if not period.is_published or period.is_demo:
        return None
    distribution = _published_distribution_for_period(session, period)
    if distribution is None:
        return None
    source = session.get(SourceDocument, distribution.source_document_id)
    run = _run_for_distribution(session, distribution)
    if source is None or run is None or source.is_demo:
        return None
    treatment, states_scope, originals = _config(run)
    component = reconciliation_for_distribution(distribution, run)
    jurisdiction, covered = _jurisdiction_reconciliation(
        session,
        distribution,
        states_scope=states_scope,
        originals=originals,
    )
    component_response = NationalReconciliation(
        status=(
            component.status
            if component.status in {"reconciled", "conflicted", "unavailable"}
            else "unavailable"
        ),
        observed_total=_money(distribution.net_distributable_amount),
        derived_total=_money(component.component_total),
        variance=_money(component.variance),
        tolerance=_money(component.tolerance),
        evidence_class=(
            "derived"
            if component.status == "reconciled"
            else "conflicted"
            if component.status == "conflicted"
            else "missing"
        ),
        basis="Official recipient components vs distributable total",
        note=component.note,
    )
    return PublishedNationalDistribution(
        reporting_period_id=str(period.id),
        reporting_label=period.reporting_label,
        revenue_month=period.revenue_month,
        published_at=distribution.published_at,
        verification_status=distribution.verification_status.value,
        reported_unit=distribution.reported_unit.value,
        derivation_treatment=treatment,
        states_scope=states_scope,
        covered_jurisdictions=covered,
        expected_jurisdictions=EXPECTED_JURISDICTIONS,
        source=NationalSource(
            source_organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            publication_date=source.publication_date,
            document_version=source.document_version,
        ),
        net_distributable_amount=_observed(distribution.net_distributable_amount),
        federal_amount=_observed(distribution.federal_amount),
        states_amount=_observed(distribution.states_amount),
        local_governments_amount=_observed(distribution.local_governments_amount),
        derivation_amount=_observed(distribution.derivation_amount),
        vat_amount=_observed(distribution.vat_amount),
        statutory_amount=_observed(distribution.statutory_amount),
        component_reconciliation=component_response,
        jurisdiction_reconciliation=jurisdiction,
    )


def latest_published_national_distribution(
    session: Session,
) -> PublishedNationalDistribution | None:
    period = session.scalar(
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
        .limit(1)
    )
    if period is None:
        return None
    return published_national_distribution(session, period)
