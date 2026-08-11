from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.fiscal_design_schemas import (
    FiscalDesignCandidate,
    FiscalDesignEvidence,
    FiscalDesignMetric,
    FiscalDesignResponse,
)
from gaiafaac_api.services.decision_packet import decision_packet

_HUNDRED = Decimal("100")


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), ".2f")


def _pct(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), ".2f")


def _apply_change(value: Decimal, change_pct: Decimal) -> Decimal:
    return value * (_HUNDRED + change_pct) / _HUNDRED


def fiscal_design(
    session: Session,
    *,
    state_slug: str,
    year: int,
    faac_shock_pct: Decimal = Decimal("-20"),
    igr_shock_pct: Decimal = Decimal("0"),
    reserve_share_pct: Decimal = Decimal("10"),
) -> FiscalDesignResponse | None:
    packet = decision_packet(session, state_slug=state_slug, year=year)
    if packet is None:
        return None

    faac = Decimal(packet.annual_net) if packet.annual_net is not None else None
    annual_igr_record = next(
        (
            record
            for record in packet.igr_records
            if record.period_type == "annual" and record.quarter is None
        ),
        None,
    )
    annual_igr = Decimal(annual_igr_record.igr_amount) if annual_igr_record is not None else None
    complete_year = packet.months_published == 12

    evidence = [
        FiscalDesignEvidence(
            evidence_domain="faac",
            label=f"{month.reporting_label} net FAAC allocation",
            value=month.net_allocation or "Unavailable",
            source_organization=month.source_organization,
            source_sha256=month.source_sha256,
            reference_path=month.proof_path,
        )
        for month in packet.months
    ]
    if annual_igr_record is not None:
        evidence.append(
            FiscalDesignEvidence(
                evidence_domain="igr",
                label=f"{year} annual IGR",
                value=annual_igr_record.igr_amount,
                source_organization=annual_igr_record.source_organization,
                source_sha256=annual_igr_record.source_sha256,
                reference_path=f"/states/{packet.state_slug}",
            )
        )

    if faac is None:
        faac_candidate = FiscalDesignCandidate(
            key="faac_shock",
            title="FAAC shock scenario",
            purpose="Measure the effect of a user-selected change to the published FAAC baseline.",
            status="insufficient_data",
            metrics=[],
            note="No published FAAC net amount is available for this state and year.",
        )
    else:
        stressed_faac = _apply_change(faac, faac_shock_pct)
        gap = max(faac - stressed_faac, Decimal("0"))
        faac_candidate = FiscalDesignCandidate(
            key="faac_shock",
            title="FAAC shock scenario",
            purpose="Measure the effect of a user-selected change to the published FAAC baseline.",
            status="available",
            metrics=[
                FiscalDesignMetric(label="Published FAAC baseline", value=_money(faac), unit="NGN"),
                FiscalDesignMetric(label="Scenario FAAC", value=_money(stressed_faac), unit="NGN"),
                FiscalDesignMetric(label="Illustrative gap", value=_money(gap), unit="NGN"),
            ],
            note=(
                "The percentage change is an explicit scenario assumption. "
                + (
                    "The baseline covers all 12 published months."
                    if complete_year
                    else "The baseline covers only published months and is not annualized."
                )
            ),
        )

    if annual_igr is None:
        igr_candidate = FiscalDesignCandidate(
            key="igr_buffer",
            title="IGR buffer scenario",
            purpose="Explore a user-selected buffer share against exact-year annual IGR evidence.",
            status="insufficient_data",
            metrics=[],
            note="No published, human-verified annual IGR record is available for this exact year.",
        )
    else:
        stressed_igr = _apply_change(annual_igr, igr_shock_pct)
        buffer_amount = stressed_igr * reserve_share_pct / _HUNDRED
        igr_candidate = FiscalDesignCandidate(
            key="igr_buffer",
            title="IGR buffer scenario",
            purpose="Explore a user-selected buffer share against exact-year annual IGR evidence.",
            status="available",
            metrics=[
                FiscalDesignMetric(
                    label="Annual IGR baseline", value=_money(annual_igr), unit="NGN"
                ),
                FiscalDesignMetric(
                    label="Scenario annual IGR", value=_money(stressed_igr), unit="NGN"
                ),
                FiscalDesignMetric(
                    label=f"Illustrative buffer at {_pct(reserve_share_pct)}%",
                    value=_money(buffer_amount),
                    unit="NGN",
                ),
            ],
            note=(
                "The buffer share is a user-selected research assumption, not a recommendation or "
                "statement that funds are available for any particular use."
            ),
        )

    if faac is None or annual_igr is None or not complete_year:
        blended_candidate = FiscalDesignCandidate(
            key="blended_revenue",
            title="Blended revenue stress scenario",
            purpose="Stress a same-year FAAC plus IGR evidence envelope without mixing periods.",
            status="insufficient_data",
            metrics=[],
            note=(
                "This scenario requires 12 published FAAC months and a published annual IGR "
                "record for the same year. Missing or partial periods are not annualized "
                "or borrowed."
            ),
        )
    else:
        stressed_faac = _apply_change(faac, faac_shock_pct)
        stressed_igr = _apply_change(annual_igr, igr_shock_pct)
        baseline = faac + annual_igr
        stressed = stressed_faac + stressed_igr
        blended_candidate = FiscalDesignCandidate(
            key="blended_revenue",
            title="Blended revenue stress scenario",
            purpose="Stress a same-year FAAC plus IGR evidence envelope without mixing periods.",
            status="available",
            metrics=[
                FiscalDesignMetric(label="Combined baseline", value=_money(baseline), unit="NGN"),
                FiscalDesignMetric(label="Scenario envelope", value=_money(stressed), unit="NGN"),
                FiscalDesignMetric(
                    label="Scenario delta", value=_money(stressed - baseline), unit="NGN"
                ),
            ],
            note=(
                "This combines only complete-year published FAAC with exact-year annual IGR. "
                "It is a hypothetical stress scenario, not a forecast of future receipts."
            ),
        )

    objective = (
        "Explore hypothetical fiscal-resilience scenarios using governed FAAC and IGR "
        "evidence."
    )

    return FiscalDesignResponse(
        state_name=packet.state_name,
        state_slug=packet.state_slug,
        state_code=packet.state_code,
        year=year,
        objective=objective,
        coverage_label=packet.coverage_label,
        faac_months_published=packet.months_published,
        faac_complete_year=complete_year,
        annual_igr_available=annual_igr_record is not None,
        faac_shock_pct=_pct(faac_shock_pct),
        igr_shock_pct=_pct(igr_shock_pct),
        reserve_share_pct=_pct(reserve_share_pct),
        assumptions=[
            f"FAAC scenario change: {_pct(faac_shock_pct)}%.",
            f"IGR scenario change: {_pct(igr_shock_pct)}%.",
            f"Illustrative IGR buffer share: {_pct(reserve_share_pct)}%.",
            "No missing periods are inferred, annualized, or substituted from another year.",
            "All scenario arithmetic uses deterministic Decimal math over governed evidence.",
        ],
        evidence=evidence,
        candidates=[faac_candidate, igr_candidate, blended_candidate],
        disclaimer=(
            "Gaia Fiscal Design Lab produces hypothetical, evidence-grounded scenario outputs for "
            "research and planning. It is not a forecast, investment recommendation, or substitute "
            "for treasury, legal, accounting, or financial review."
        ),
    )
