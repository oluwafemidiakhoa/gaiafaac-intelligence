from __future__ import annotations

from dataclasses import dataclass

from gaiafaac_api.database.enums import PlanCode


@dataclass(frozen=True)
class Entitlements:
    """What a plan grants. Basic official-source access (the latest verified month) is
    always free and is never represented here — it is not gated by any plan."""

    label: str
    price_usd_monthly: int
    historical_access: bool
    downloads: bool
    api_access: bool
    api_rate_limit_per_day: int


PLAN_ENTITLEMENTS: dict[PlanCode, Entitlements] = {
    PlanCode.FREE: Entitlements(
        label="Free",
        price_usd_monthly=0,
        historical_access=False,
        downloads=False,
        api_access=False,
        api_rate_limit_per_day=0,
    ),
    PlanCode.ANALYST: Entitlements(
        label="Analyst",
        price_usd_monthly=49,
        historical_access=True,
        downloads=True,
        api_access=False,
        api_rate_limit_per_day=0,
    ),
    PlanCode.TEAM: Entitlements(
        label="Team",
        price_usd_monthly=199,
        historical_access=True,
        downloads=True,
        api_access=False,
        api_rate_limit_per_day=0,
    ),
    PlanCode.API: Entitlements(
        label="API",
        price_usd_monthly=299,
        historical_access=True,
        downloads=True,
        api_access=True,
        api_rate_limit_per_day=5000,
    ),
}


def entitlements_for(plan_code: str) -> Entitlements:
    """Resolve entitlements for a plan code, defaulting to FREE for anything unknown."""
    try:
        return PLAN_ENTITLEMENTS[PlanCode(plan_code)]
    except ValueError:
        return PLAN_ENTITLEMENTS[PlanCode.FREE]
