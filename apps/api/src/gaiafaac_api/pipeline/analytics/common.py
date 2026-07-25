from __future__ import annotations

import hashlib
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ForecastMethod
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument

ANALYTICS_NAMESPACE = "gaiafaac-analytics-v1"
ANALYTICS_PERIOD_PREFIX = "DEMO ANALYTICS —"
ANALYTICS_SOURCE_ORG = "GaiaFAAC Intelligence (DEMO ANALYTICS)"
ANALYTICS_SOURCE_SHA256 = hashlib.sha256(ANALYTICS_NAMESPACE.encode("utf-8")).hexdigest()
DEMO_DATA_LABEL = "DEMO DATA - NOT REAL FAAC DATA"

OIL_STATES = frozenset({"AK", "BY", "DE", "RI", "ON", "ED", "IM", "AB"})
START_YEAR = 2096
PERIOD_COUNT = 36
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
FORECAST_TARGET = date(2099, 1, 1)

VOLATILITY_WINDOW = 12
VOLATILITY_MIN_OBS = 3
FORECAST_MIN_HISTORY = 6
FORECAST_WINDOW = 12
FORECAST_Z = Decimal("1.96")
CENTS = Decimal("0.01")
RATIO_QUANT = Decimal("0.000001")


@dataclass(frozen=True)
class IndicatorSpec:
    reporting_period_id: uuid.UUID
    state_id: uuid.UUID
    source_document_id: uuid.UUID
    indicator_type: str
    indicator_name: str
    value: Decimal
    unit: str
    methodology: str


@dataclass(frozen=True)
class ForecastSpec:
    state_id: uuid.UUID
    source_document_id: uuid.UUID
    target_period: date
    method: ForecastMethod
    point_estimate: Decimal
    lower_bound: Decimal
    upper_bound: Decimal
    training_start: date
    training_end: date
    metrics: dict[str, Any] = field(default_factory=dict)


def _hash_unit(key: str) -> Decimal:
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    value = int.from_bytes(digest[:8], "big")
    return Decimal(value % 1_000_000) / Decimal(1_000_000)


def deterministic_unit(state_code: str, year: int, month: int, salt: str = "") -> Decimal:
    return _hash_unit(f"{ANALYTICS_NAMESPACE}:{salt}:{state_code}:{year:04d}-{month:02d}")


def state_base(state_code: str) -> Decimal:
    digest = hashlib.sha256(f"{ANALYTICS_NAMESPACE}:base:{state_code}".encode()).digest()
    value = int.from_bytes(digest[:8], "big")
    return Decimal(1_000_000_000) + Decimal(value % 5_000_000_000)


def seasonal_factor(month: int) -> Decimal:
    return (Decimal("1.00") + (Decimal(month) - Decimal("6")) / Decimal("100")).quantize(
        Decimal("0.01")
    )


def decimal_mean(values: list[Decimal]) -> Decimal:
    return statistics.mean(values)


def decimal_pstdev(values: list[Decimal]) -> Decimal:
    return statistics.pstdev(values)


def analytics_source(session: Session) -> SourceDocument | None:
    return session.scalar(
        select(SourceDocument).where(SourceDocument.sha256 == ANALYTICS_SOURCE_SHA256)
    )


def analytics_periods(session: Session) -> list[ReportingPeriod]:
    return list(
        session.scalars(
            select(ReportingPeriod)
            .where(ReportingPeriod.reporting_label.like(f"{ANALYTICS_PERIOD_PREFIX}%"))
            .order_by(ReportingPeriod.revenue_month)
        )
    )


def latest_analytics_period(session: Session) -> ReportingPeriod | None:
    periods = analytics_periods(session)
    return periods[-1] if periods else None
