from __future__ import annotations

from dataclasses import dataclass

from gaiafaac_api.database.enums import PlanCode


@dataclass(frozen=True)
class Entitlements:
    """What a plan grants. Commercial pricing is configured separately."""

    label: str
    historical_access: bool
    downloads: bool
    api_access: bool
    api_rate_limit_per_day: int
    max_users: int


PLAN_ENTITLEMENTS: dict[PlanCode, Entitlements] = {
    PlanCode.FREE: Entitlements(
        label="Free",
        historical_access=False,
        downloads=False,
        api_access=False,
        api_rate_limit_per_day=0,
        max_users=1,
    ),
    PlanCode.ANALYST: Entitlements(
        label="Analyst",
        historical_access=True,
        downloads=True,
        api_access=False,
        api_rate_limit_per_day=0,
        max_users=1,
    ),
    PlanCode.TEAM: Entitlements(
        label="Team",
        historical_access=True,
        downloads=True,
        api_access=False,
        api_rate_limit_per_day=0,
        max_users=10,
    ),
    PlanCode.API: Entitlements(
        label="API",
        historical_access=True,
        downloads=True,
        api_access=True,
        api_rate_limit_per_day=5000,
        max_users=10,
    ),
}


def entitlements_for(plan_code: str) -> Entitlements:
    """Resolve entitlements for a plan code, defaulting to FREE for anything unknown."""
    try:
        return PLAN_ENTITLEMENTS[PlanCode(plan_code)]
    except ValueError:
        return PLAN_ENTITLEMENTS[PlanCode.FREE]
