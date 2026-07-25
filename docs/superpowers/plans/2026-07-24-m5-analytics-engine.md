# M5 Analytics Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Milestone 5 analytics engine — a labelled-synthetic multi-period demo dataset, four deterministic analytics (rankings, volatility, revenue-dependency, forecasting) persisted to existing tables, and read-only demo-constrained `/api/v1` endpoints.

**Architecture:** A CLI-invoked pipeline generates a synthetic 37-state × 36-month demo dataset, then computes analytics deterministically from the stored figures and writes them to the existing `state_indicators` and `forecasts` tables (marked `is_demo`, unpublished). Read endpoints serve the stored rows. All money is `Decimal`; insufficient data fails closed (omitted, never zero).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, standard-library `statistics`/`hashlib`/`decimal`. Tests: pytest on SQLite in-memory (existing `conftest`).

## Global Constraints

- Python `>=3.12`; **no new third-party dependencies** (stdlib only).
- Money uses `Decimal`, quantized to `Decimal("0.01")`; ratios use the `NUMERIC` precise columns. **Never** use `float` for money.
- Every generated/computed row: `is_demo=True`, `is_published=False`, `verification_status=VerificationStatus.PENDING`. Never set `is_published=True`.
- Demo label literal, verbatim: `"DEMO DATA - NOT REAL FAAC DATA"`.
- Fail closed: insufficient history → the analytic is omitted (absent/`None`), never zero or fabricated.
- Forecasts are always estimates: carry an interval with `lower_bound <= point_estimate <= upper_bound`; never presented as a reported allocation.
- **No new database migration** — `state_indicators` and `forecasts` already exist.
- Do not disturb Milestone 4: analytics periods end at 2098-12, so `latest_demo_period` still resolves to 2099-01.
- Analytics code scopes strictly to the analytics source document / `"DEMO ANALYTICS —"` periods.
- Ruff lint rules `E,F,I,UP,B,SIM`, line length 100 (`apps/api/pyproject.toml`).
- All new API/pipeline code lives in the `gaiafaac_api` package under `apps/api/src/`, following existing module patterns.
- Commit messages end with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. Commit steps assume the user has authorized commits for this build; otherwise stage only.

---

## Setup (before Task 1)

Create a feature branch off `main` (never commit analytics work directly to `main`):

```bash
git checkout -b feat/m5-analytics-engine
```

Run the existing suite once to confirm a green baseline:

```bash
python -m pytest apps/api/tests -q
```
Expected: all pass.

---

## Task 1: Analytics common module (constants, deterministic + stats helpers, shared specs)

**Files:**
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/__init__.py`
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/common.py`
- Test: `apps/api/tests/test_analytics_common.py`

**Interfaces:**
- Produces (pure): `deterministic_unit(state_code: str, year: int, month: int, salt: str = "") -> Decimal` in `[0,1)`; `state_base(state_code: str) -> Decimal`; `seasonal_factor(month: int) -> Decimal`; `decimal_mean(values: list[Decimal]) -> Decimal`; `decimal_pstdev(values: list[Decimal]) -> Decimal`.
- Produces (DB, tested in Task 2): `analytics_source(session) -> SourceDocument | None`; `analytics_periods(session) -> list[ReportingPeriod]`; `latest_analytics_period(session) -> ReportingPeriod | None`.
- Produces (dataclasses): `IndicatorSpec`, `ForecastSpec`.
- Produces (constants): `ANALYTICS_NAMESPACE`, `ANALYTICS_PERIOD_PREFIX`, `ANALYTICS_SOURCE_ORG`, `ANALYTICS_SOURCE_SHA256`, `DEMO_DATA_LABEL`, `OIL_STATES`, `START_YEAR`, `PERIOD_COUNT`, `MONTH_NAMES`, `FORECAST_TARGET`, `VOLATILITY_WINDOW`, `VOLATILITY_MIN_OBS`, `FORECAST_MIN_HISTORY`, `FORECAST_WINDOW`, `FORECAST_Z`, `CENTS`, `RATIO_QUANT`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_common.py
from decimal import Decimal

from gaiafaac_api.pipeline.analytics.common import (
    decimal_mean,
    decimal_pstdev,
    deterministic_unit,
    seasonal_factor,
    state_base,
)


def test_deterministic_unit_is_stable_and_bounded() -> None:
    a = deterministic_unit("LA", 2097, 3)
    b = deterministic_unit("LA", 2097, 3)
    assert a == b
    assert Decimal("0") <= a < Decimal("1")
    assert deterministic_unit("LA", 2097, 3, salt="ded") != a


def test_state_base_is_stable_and_in_range() -> None:
    base = state_base("KN")
    assert base == state_base("KN")
    assert Decimal("1000000000") <= base < Decimal("6000000000")


def test_seasonal_factor_centres_near_one() -> None:
    assert seasonal_factor(6) == Decimal("1.00")
    assert seasonal_factor(1) < seasonal_factor(12)


def test_decimal_stats() -> None:
    values = [Decimal("100"), Decimal("200"), Decimal("300")]
    assert decimal_mean(values) == Decimal("200")
    assert decimal_pstdev(values) == Decimal("200").sqrt() * Decimal("0") + Decimal(
        "81.6496580927726032732428024"
    ).quantize(Decimal("0.0000001")) or decimal_pstdev(values) > Decimal("81")
```

> Note: the stats assertion above is intentionally loose on the irrational value; the real check is `decimal_pstdev([100,200,300])` ≈ 81.6497. Replace with `assert decimal_pstdev(values).quantize(Decimal("0.0001")) == Decimal("81.6497")`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_common.py -v`
Expected: FAIL with `ModuleNotFoundError: gaiafaac_api.pipeline.analytics.common`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/__init__.py
```

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/common.py
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
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
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
```

- [ ] **Step 4: Fix the loose stats assertion, then run tests**

Edit the last test to:
```python
def test_decimal_stats() -> None:
    values = [Decimal("100"), Decimal("200"), Decimal("300")]
    assert decimal_mean(values) == Decimal("200")
    assert decimal_pstdev(values).quantize(Decimal("0.0001")) == Decimal("81.6497")
```
Run: `python -m pytest apps/api/tests/test_analytics_common.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/analytics/__init__.py apps/api/src/gaiafaac_api/pipeline/analytics/common.py apps/api/tests/test_analytics_common.py
git commit -m "feat(analytics): add analytics common constants and helpers"
```

---

## Task 2: Synthetic multi-period dataset generator

**Files:**
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/dataset.py`
- Test: `apps/api/tests/test_analytics_dataset.py`

**Interfaces:**
- Consumes: `common` constants/helpers; `seed_states`; models `ReportingPeriod`, `SourceDocument`, `StateAllocation`, `StateAllocationComponent`, `State`.
- Produces: `generate_analytics_dataset(session) -> DatasetSummary` with fields `periods:int, allocations:int, components:int, source_document_id:uuid.UUID`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_dataset.py
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.analytics.common import latest_analytics_period
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset


def test_dataset_shape_and_invariants(session: Session) -> None:
    summary = generate_analytics_dataset(session)
    assert summary.periods == 36
    assert summary.allocations == 36 * 37

    allocations = list(session.scalars(select(StateAllocation)))
    assert allocations
    for allocation in allocations:
        assert allocation.is_demo is True
        assert allocation.is_published is False
        assert allocation.gross_total - allocation.total_deductions == allocation.net_allocation

    latest = latest_analytics_period(session)
    assert latest is not None
    assert latest.revenue_month == date(2098, 12, 1)


def test_dataset_is_idempotent(session: Session) -> None:
    first = generate_analytics_dataset(session)
    second = generate_analytics_dataset(session)
    assert (first.periods, first.allocations) == (second.periods, second.allocations)
    assert session.scalar(select(func.count()).select_from(StateAllocation)) == 36 * 37


def test_dataset_does_not_change_m4_latest_demo_period(session: Session) -> None:
    from gaiafaac_api.database.seeds import seed_demo_allocations
    from gaiafaac_api.services.demo_data import latest_demo_period

    seed_demo_allocations(session, _demo_csv())
    generate_analytics_dataset(session)
    period = latest_demo_period(session)
    assert period is not None
    assert period.revenue_month == date(2099, 1, 1)


def _demo_csv():
    from pathlib import Path

    return Path(__file__).resolve().parents[3] / "database/seeds/demo_state_allocations.csv"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_dataset.py -v`
Expected: FAIL with `ModuleNotFoundError: ...analytics.dataset`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/dataset.py
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ComponentType,
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    StateAllocationComponent,
)
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.analytics.common import (
    ANALYTICS_PERIOD_PREFIX,
    ANALYTICS_SOURCE_ORG,
    ANALYTICS_SOURCE_SHA256,
    CENTS,
    MONTH_NAMES,
    OIL_STATES,
    PERIOD_COUNT,
    START_YEAR,
    analytics_source,
    deterministic_unit,
    seasonal_factor,
    state_base,
)


@dataclass(frozen=True)
class DatasetSummary:
    periods: int
    allocations: int
    components: int
    source_document_id: uuid.UUID


def _next_month(year: int, month: int) -> date:
    return date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)


def _split(total: Decimal, shares: list[Decimal]) -> list[Decimal]:
    parts = [(total * share).quantize(CENTS) for share in shares[:-1]]
    parts.append(total - sum(parts))
    return parts


def _component_shares(code: str) -> list[tuple[ComponentType, str, Decimal]]:
    if code in OIL_STATES:
        return [
            (ComponentType.STATUTORY_ALLOCATION, "Statutory allocation", Decimal("0.55")),
            (ComponentType.VAT, "VAT", Decimal("0.20")),
            (ComponentType.DERIVATION, "Derivation", Decimal("0.25")),
        ]
    return [
        (ComponentType.STATUTORY_ALLOCATION, "Statutory allocation", Decimal("0.75")),
        (ComponentType.VAT, "VAT", Decimal("0.25")),
    ]


def _summarize(session: Session, source: SourceDocument) -> DatasetSummary:
    periods = session.scalar(
        select(func.count())
        .select_from(ReportingPeriod)
        .where(ReportingPeriod.reporting_label.like(f"{ANALYTICS_PERIOD_PREFIX}%"))
    )
    allocations = session.scalar(
        select(func.count())
        .select_from(StateAllocation)
        .where(StateAllocation.source_document_id == source.id)
    )
    components = session.scalar(
        select(func.count())
        .select_from(StateAllocationComponent)
        .join(StateAllocation, StateAllocationComponent.state_allocation_id == StateAllocation.id)
        .where(StateAllocation.source_document_id == source.id)
    )
    return DatasetSummary(periods or 0, allocations or 0, components or 0, source.id)


def generate_analytics_dataset(session: Session) -> DatasetSummary:
    """Create a labelled synthetic 37-state x 36-month demo dataset (idempotent)."""
    seed_states(session)
    existing = analytics_source(session)
    if existing is not None:
        return _summarize(session, existing)

    source = SourceDocument(
        source_organization=ANALYTICS_SOURCE_ORG,
        original_filename="demo-analytics-synthetic.dataset",
        storage_path="(synthetic; generated in-process, no file)",
        sha256=ANALYTICS_SOURCE_SHA256,
        mime_type="application/x-gaiafaac-demo",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.DEMO,
        document_version="analytics-v1",
        is_demo=True,
    )
    session.add(source)
    session.flush()

    states = list(session.scalars(select(State).order_by(State.code)))
    components_written = 0
    for idx in range(PERIOD_COUNT):
        year = START_YEAR + idx // 12
        month = idx % 12 + 1
        period = ReportingPeriod(
            revenue_month=date(year, month, 1),
            faac_meeting_date=_next_month(year, month),
            publication_date=_next_month(year, month),
            reporting_label=f"{ANALYTICS_PERIOD_PREFIX} {MONTH_NAMES[month - 1]} {year} synthetic period",
            source_status=SourceStatus.DEMO,
            verification_status=VerificationStatus.PENDING,
            is_demo=True,
            is_published=False,
        )
        session.add(period)
        session.flush()
        for state in states:
            unit = deterministic_unit(state.code, year, month)
            gross = (
                state_base(state.code)
                * seasonal_factor(month)
                * (Decimal("0.9") + Decimal("0.2") * unit)
            ).quantize(CENTS)
            ded_rate = Decimal("0.05") + Decimal("0.10") * deterministic_unit(
                state.code, year, month, salt="ded"
            )
            deductions = (gross * ded_rate).quantize(CENTS)
            net = gross - deductions
            allocation = StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=source.id,
                gross_total=gross,
                total_deductions=deductions,
                net_allocation=net,
                gross_total_original=str(gross),
                total_deductions_original=str(deductions),
                net_allocation_original=str(net),
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.PENDING,
                is_demo=True,
                is_published=False,
            )
            session.add(allocation)
            session.flush()
            shares = _component_shares(state.code)
            share_values = [share for _type, _name, share in shares]
            gross_parts = _split(gross, share_values)
            ded_parts = _split(deductions, share_values)
            net_parts = _split(net, share_values)
            for (ctype, cname, _share), cg, cd, cn in zip(
                shares, gross_parts, ded_parts, net_parts, strict=True
            ):
                session.add(
                    StateAllocationComponent(
                        state_allocation_id=allocation.id,
                        component_type=ctype,
                        component_name=cname,
                        gross_amount=cg,
                        deduction_amount=cd,
                        net_amount=cn,
                        gross_amount_original=str(cg),
                        deduction_amount_original=str(cd),
                        net_amount_original=str(cn),
                        reported_unit=ReportedUnit.NAIRA,
                    )
                )
                components_written += 1

    session.commit()
    return _summarize(session, source)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest apps/api/tests/test_analytics_dataset.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/analytics/dataset.py apps/api/tests/test_analytics_dataset.py
git commit -m "feat(analytics): generate labelled synthetic multi-period demo dataset"
```

---

## Task 3: Rankings analytic

**Files:**
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/rankings.py`
- Test: `apps/api/tests/test_analytics_rankings.py`

**Interfaces:**
- Consumes: `common`, `generate_analytics_dataset`, models.
- Produces: `compute_rankings(session) -> list[IndicatorSpec]` — for the latest analytics period, one `ranking`/`net_allocation_rank` (value 1..37) and, where a prior period exists, one `ranking`/`net_allocation_rank_change` per state.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_rankings.py
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import State, StateAllocation
from gaiafaac_api.pipeline.analytics.common import latest_analytics_period
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.rankings import compute_rankings


def test_rankings_match_net_ordering(session: Session) -> None:
    generate_analytics_dataset(session)
    latest = latest_analytics_period(session)
    assert latest is not None

    nets = {
        state_id: net
        for state_id, net in session.execute(
            select(StateAllocation.state_id, StateAllocation.net_allocation).where(
                StateAllocation.reporting_period_id == latest.id
            )
        )
    }
    expected_order = [sid for sid, _net in sorted(nets.items(), key=lambda kv: kv[1], reverse=True)]

    specs = compute_rankings(session)
    ranks = {
        spec.state_id: spec.value
        for spec in specs
        if spec.indicator_name == "net_allocation_rank"
    }
    assert len(ranks) == 37
    assert ranks[expected_order[0]] == Decimal("1")
    assert ranks[expected_order[-1]] == Decimal("37")
    assert any(spec.indicator_name == "net_allocation_rank_change" for spec in specs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_rankings.py -v`
Expected: FAIL with `ModuleNotFoundError: ...analytics.rankings`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/rankings.py
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.analytics.common import (
    IndicatorSpec,
    analytics_periods,
    analytics_source,
)


def _rank_map(session: Session, period_id: uuid.UUID) -> dict[uuid.UUID, int]:
    rows = session.execute(
        select(StateAllocation.state_id, StateAllocation.net_allocation)
        .where(
            StateAllocation.reporting_period_id == period_id,
            StateAllocation.net_allocation.is_not(None),
        )
        .order_by(StateAllocation.net_allocation.desc())
    ).all()
    return {state_id: index for index, (state_id, _net) in enumerate(rows, start=1)}


def compute_rankings(session: Session) -> list[IndicatorSpec]:
    source = analytics_source(session)
    periods = analytics_periods(session)
    if source is None or not periods:
        return []
    latest = periods[-1]
    previous: ReportingPeriod | None = periods[-2] if len(periods) >= 2 else None
    current = _rank_map(session, latest.id)
    prior = _rank_map(session, previous.id) if previous is not None else {}

    specs: list[IndicatorSpec] = []
    for state_id, rank in current.items():
        specs.append(
            IndicatorSpec(
                reporting_period_id=latest.id,
                state_id=state_id,
                source_document_id=source.id,
                indicator_type="ranking",
                indicator_name="net_allocation_rank",
                value=Decimal(rank),
                unit="rank",
                methodology=f"Descending net_allocation rank for {latest.reporting_label}.",
            )
        )
        if state_id in prior:
            specs.append(
                IndicatorSpec(
                    reporting_period_id=latest.id,
                    state_id=state_id,
                    source_document_id=source.id,
                    indicator_type="ranking",
                    indicator_name="net_allocation_rank_change",
                    value=Decimal(prior[state_id] - rank),
                    unit="rank_delta",
                    methodology="Prior-period rank minus current rank (positive = moved up).",
                )
            )
    return specs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_analytics_rankings.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/analytics/rankings.py apps/api/tests/test_analytics_rankings.py
git commit -m "feat(analytics): compute net-allocation rankings and rank change"
```

---

## Task 4: Volatility analytic

**Files:**
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/volatility.py`
- Test: `apps/api/tests/test_analytics_volatility.py`

**Interfaces:**
- Consumes: `common`, dataset, models.
- Produces: `coefficient_of_variation(values: list[Decimal]) -> Decimal | None` (pure); `compute_volatility(session) -> list[IndicatorSpec]` (`volatility`/`net_allocation_cv`, unit `ratio`).

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_volatility.py
from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.volatility import (
    coefficient_of_variation,
    compute_volatility,
)


def test_cv_pure_helper() -> None:
    assert coefficient_of_variation([]) is None
    assert coefficient_of_variation([Decimal("100"), Decimal("100")]) is None  # < min obs
    assert coefficient_of_variation([Decimal("0"), Decimal("0"), Decimal("0")]) is None  # zero mean
    cv = coefficient_of_variation([Decimal("100"), Decimal("200"), Decimal("300")])
    assert cv is not None
    assert cv.quantize(Decimal("0.0001")) == Decimal("0.4082")


def test_compute_volatility_covers_all_states(session: Session) -> None:
    generate_analytics_dataset(session)
    specs = compute_volatility(session)
    assert len(specs) == 37
    assert all(spec.indicator_name == "net_allocation_cv" for spec in specs)
    assert all(spec.value >= Decimal("0") for spec in specs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_volatility.py -v`
Expected: FAIL with `ModuleNotFoundError: ...analytics.volatility`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/volatility.py
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.analytics.common import (
    RATIO_QUANT,
    VOLATILITY_MIN_OBS,
    VOLATILITY_WINDOW,
    IndicatorSpec,
    analytics_periods,
    analytics_source,
    decimal_mean,
    decimal_pstdev,
)


def coefficient_of_variation(values: list[Decimal]) -> Decimal | None:
    cleaned = [value for value in values if value is not None]
    if len(cleaned) < VOLATILITY_MIN_OBS:
        return None
    mean = decimal_mean(cleaned)
    if mean == 0:
        return None
    return (decimal_pstdev(cleaned) / mean).quantize(RATIO_QUANT)


def compute_volatility(session: Session) -> list[IndicatorSpec]:
    source = analytics_source(session)
    periods = analytics_periods(session)
    if source is None or not periods:
        return []
    window = periods[-VOLATILITY_WINDOW:]
    window_ids = [period.id for period in window]
    latest = periods[-1]

    rows = session.execute(
        select(StateAllocation.state_id, StateAllocation.net_allocation)
        .join(ReportingPeriod, StateAllocation.reporting_period_id == ReportingPeriod.id)
        .where(StateAllocation.reporting_period_id.in_(window_ids))
        .order_by(StateAllocation.state_id, ReportingPeriod.revenue_month)
    ).all()

    by_state: dict = {}
    for state_id, net in rows:
        by_state.setdefault(state_id, []).append(net)

    specs: list[IndicatorSpec] = []
    for state_id, nets in by_state.items():
        cv = coefficient_of_variation(nets)
        if cv is None:
            continue
        specs.append(
            IndicatorSpec(
                reporting_period_id=latest.id,
                state_id=state_id,
                source_document_id=source.id,
                indicator_type="volatility",
                indicator_name="net_allocation_cv",
                value=cv,
                unit="ratio",
                methodology=(
                    f"Coefficient of variation (population) of net_allocation over the "
                    f"trailing {len(window)} periods ending {latest.reporting_label}."
                ),
            )
        )
    return specs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_analytics_volatility.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/analytics/volatility.py apps/api/tests/test_analytics_volatility.py
git commit -m "feat(analytics): compute net-allocation volatility (coefficient of variation)"
```

---

## Task 5: Revenue-dependency analytic

**Files:**
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/dependency.py`
- Test: `apps/api/tests/test_analytics_dependency.py`

**Interfaces:**
- Consumes: `common`, dataset, models.
- Produces: `component_shares(pairs: list[tuple[str, Decimal]]) -> tuple[dict[str, Decimal], Decimal] | None` (pure — returns per-type share + HHI); `compute_dependency(session) -> list[IndicatorSpec]` (`dependency`/`{component_type}_net_share` + `dependency`/`net_concentration_hhi`).

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_dependency.py
from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.dependency import component_shares, compute_dependency


def test_component_shares_and_hhi() -> None:
    assert component_shares([]) is None
    result = component_shares([("statutory_allocation", Decimal("75")), ("vat", Decimal("25"))])
    assert result is not None
    shares, hhi = result
    assert shares["statutory_allocation"] == Decimal("0.750000")
    assert shares["vat"] == Decimal("0.250000")
    assert hhi == Decimal("0.625000")


def test_compute_dependency_emits_shares_and_hhi(session: Session) -> None:
    generate_analytics_dataset(session)
    specs = compute_dependency(session)
    names = {spec.indicator_name for spec in specs}
    assert "net_concentration_hhi" in names
    assert "statutory_allocation_net_share" in names
    hhi_specs = [spec for spec in specs if spec.indicator_name == "net_concentration_hhi"]
    assert len(hhi_specs) == 37
    assert all(Decimal("0") < spec.value <= Decimal("1") for spec in hhi_specs)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_dependency.py -v`
Expected: FAIL with `ModuleNotFoundError: ...analytics.dependency`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/dependency.py
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import StateAllocation, StateAllocationComponent
from gaiafaac_api.pipeline.analytics.common import (
    RATIO_QUANT,
    IndicatorSpec,
    analytics_source,
    latest_analytics_period,
)


def component_shares(
    pairs: list[tuple[str, Decimal]],
) -> tuple[dict[str, Decimal], Decimal] | None:
    total = sum((net for _type, net in pairs), Decimal("0"))
    if not pairs or total <= 0:
        return None
    shares = {ctype: (net / total).quantize(RATIO_QUANT) for ctype, net in pairs}
    hhi = sum((share * share for share in shares.values()), Decimal("0")).quantize(RATIO_QUANT)
    return shares, hhi


def compute_dependency(session: Session) -> list[IndicatorSpec]:
    source = analytics_source(session)
    latest = latest_analytics_period(session)
    if source is None or latest is None:
        return []

    rows = session.execute(
        select(
            StateAllocation.state_id,
            StateAllocationComponent.component_type,
            StateAllocationComponent.net_amount,
        )
        .join(
            StateAllocationComponent,
            StateAllocationComponent.state_allocation_id == StateAllocation.id,
        )
        .where(StateAllocation.reporting_period_id == latest.id)
    ).all()

    by_state: dict[uuid.UUID, list[tuple[str, Decimal]]] = {}
    for state_id, component_type, net in rows:
        if net is None:
            continue
        by_state.setdefault(state_id, []).append((str(component_type), net))

    specs: list[IndicatorSpec] = []
    for state_id, pairs in by_state.items():
        result = component_shares(pairs)
        if result is None:
            continue
        shares, hhi = result
        for component_type, share in shares.items():
            specs.append(
                IndicatorSpec(
                    reporting_period_id=latest.id,
                    state_id=state_id,
                    source_document_id=source.id,
                    indicator_type="dependency",
                    indicator_name=f"{component_type}_net_share",
                    value=share,
                    unit="ratio",
                    methodology=f"Share of net allocation from {component_type} for {latest.reporting_label}.",
                )
            )
        specs.append(
            IndicatorSpec(
                reporting_period_id=latest.id,
                state_id=state_id,
                source_document_id=source.id,
                indicator_type="dependency",
                indicator_name="net_concentration_hhi",
                value=hhi,
                unit="index",
                methodology="Herfindahl-Hirschman index (sum of squared component net shares).",
            )
        )
    return specs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_analytics_dependency.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/analytics/dependency.py apps/api/tests/test_analytics_dependency.py
git commit -m "feat(analytics): compute revenue-dependency shares and concentration index"
```

---

## Task 6: Forecasting analytic

**Files:**
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/forecasting.py`
- Test: `apps/api/tests/test_analytics_forecasting.py`

**Interfaces:**
- Consumes: `common`, dataset, models.
- Produces: `ForecastPoint` dataclass (`point, lower, upper, residual_stdev, mae, rmse, observations, window: int`); `moving_average_forecast(history: list[Decimal]) -> ForecastPoint | None`; `compute_forecasts(session) -> list[ForecastSpec]`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_forecasting.py
from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.forecasting import (
    moving_average_forecast,
    compute_forecasts,
)


def test_forecast_requires_min_history() -> None:
    assert moving_average_forecast([Decimal("1")] * 5) is None


def test_forecast_point_and_bounds_ordering() -> None:
    history = [Decimal(n) for n in range(1, 25)]  # 24 periods
    forecast = moving_average_forecast(history)
    assert forecast is not None
    assert forecast.lower <= forecast.point <= forecast.upper
    assert forecast.observations >= 1


def test_compute_forecasts_are_estimates_for_all_states(session: Session) -> None:
    generate_analytics_dataset(session)
    specs = compute_forecasts(session)
    assert len(specs) == 37
    for spec in specs:
        assert spec.lower_bound <= spec.point_estimate <= spec.upper_bound
        assert spec.target_period.year == 2099
        assert "residual_stdev" in spec.metrics
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_forecasting.py -v`
Expected: FAIL with `ModuleNotFoundError: ...analytics.forecasting`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/forecasting.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ForecastMethod
from gaiafaac_api.database.models import ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.analytics.common import (
    CENTS,
    FORECAST_MIN_HISTORY,
    FORECAST_TARGET,
    FORECAST_WINDOW,
    FORECAST_Z,
    ForecastSpec,
    analytics_periods,
    analytics_source,
    decimal_mean,
    decimal_pstdev,
)


@dataclass(frozen=True)
class ForecastPoint:
    point: Decimal
    lower: Decimal
    upper: Decimal
    residual_stdev: Decimal
    mae: Decimal
    rmse: Decimal
    observations: int
    window: int


def moving_average_forecast(history: list[Decimal]) -> ForecastPoint | None:
    values = [value for value in history if value is not None]
    if len(values) < FORECAST_MIN_HISTORY:
        return None
    window = min(FORECAST_WINDOW, len(values) - 1)
    point = decimal_mean(values[-window:]).quantize(CENTS)
    residuals = [
        values[t] - decimal_mean(values[t - window : t]) for t in range(window, len(values))
    ]
    residual_stdev = decimal_pstdev(residuals) if residuals else Decimal("0")
    half_width = (FORECAST_Z * residual_stdev).quantize(CENTS)
    mae = decimal_mean([abs(r) for r in residuals]).quantize(CENTS) if residuals else Decimal("0")
    rmse = (
        decimal_mean([r * r for r in residuals]).sqrt().quantize(CENTS)
        if residuals
        else Decimal("0")
    )
    return ForecastPoint(
        point=point,
        lower=point - half_width,
        upper=point + half_width,
        residual_stdev=residual_stdev.quantize(CENTS),
        mae=mae,
        rmse=rmse,
        observations=len(residuals),
        window=window,
    )


def compute_forecasts(session: Session) -> list[ForecastSpec]:
    source = analytics_source(session)
    periods = analytics_periods(session)
    if source is None or not periods:
        return []
    period_ids = [period.id for period in periods]
    training_start = periods[0].revenue_month
    training_end = periods[-1].revenue_month

    rows = session.execute(
        select(StateAllocation.state_id, StateAllocation.net_allocation)
        .join(ReportingPeriod, StateAllocation.reporting_period_id == ReportingPeriod.id)
        .where(StateAllocation.reporting_period_id.in_(period_ids))
        .order_by(StateAllocation.state_id, ReportingPeriod.revenue_month)
    ).all()

    by_state: dict = {}
    for state_id, net in rows:
        by_state.setdefault(state_id, []).append(net)

    specs: list[ForecastSpec] = []
    for state_id, history in by_state.items():
        forecast = moving_average_forecast(history)
        if forecast is None:
            continue
        specs.append(
            ForecastSpec(
                state_id=state_id,
                source_document_id=source.id,
                target_period=FORECAST_TARGET,
                method=ForecastMethod.MOVING_AVERAGE,
                point_estimate=forecast.point,
                lower_bound=forecast.lower,
                upper_bound=forecast.upper,
                training_start=training_start,
                training_end=training_end,
                metrics={
                    "residual_stdev": str(forecast.residual_stdev),
                    "mae": str(forecast.mae),
                    "rmse": str(forecast.rmse),
                    "observations": forecast.observations,
                    "window": forecast.window,
                    "is_estimate": True,
                },
            )
        )
    return specs
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_analytics_forecasting.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/analytics/forecasting.py apps/api/tests/test_analytics_forecasting.py
git commit -m "feat(analytics): moving-average forecasting with uncertainty interval"
```

---

## Task 7: Orchestrator — persist analytics (idempotent recompute)

**Files:**
- Create: `apps/api/src/gaiafaac_api/pipeline/analytics/run.py`
- Test: `apps/api/tests/test_analytics_run.py`

**Interfaces:**
- Consumes: all four compute functions, `analytics_source`, models `StateIndicator`, `Forecast`.
- Produces: `AnalyticsRunResult` (`indicators:int, forecasts:int`); `compute_analytics(session) -> AnalyticsRunResult` — deletes prior analytics rows by `source_document_id`, then inserts fresh; sets `is_demo=True`, `verification_status=PENDING`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_run.py
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import Forecast, StateIndicator
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics


def test_compute_analytics_persists_and_is_idempotent(session: Session) -> None:
    generate_analytics_dataset(session)
    first = compute_analytics(session)
    assert first.indicators > 0
    assert first.forecasts == 37

    indicators_after_first = session.scalar(select(func.count()).select_from(StateIndicator))
    second = compute_analytics(session)
    indicators_after_second = session.scalar(select(func.count()).select_from(StateIndicator))
    assert indicators_after_first == indicators_after_second
    assert (first.indicators, first.forecasts) == (second.indicators, second.forecasts)

    assert all(
        indicator.is_demo is False  # StateIndicator has no is_demo; verify status instead
        or indicator.verification_status is VerificationStatus.PENDING
        for indicator in session.scalars(select(StateIndicator))
    )
    assert all(
        forecast.is_demo is True and forecast.is_published is False
        for forecast in session.scalars(select(Forecast))
    )
```

> Note: `StateIndicator` has no `is_demo` column (it inherits lineage from its demo source/period). The assertion above only checks `verification_status`. Simplify to:
> ```python
> assert all(i.verification_status is VerificationStatus.PENDING for i in session.scalars(select(StateIndicator)))
> ```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_run.py -v`
Expected: FAIL with `ModuleNotFoundError: ...analytics.run`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/analytics/run.py
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import Forecast, StateIndicator
from gaiafaac_api.pipeline.analytics.common import analytics_source
from gaiafaac_api.pipeline.analytics.dependency import compute_dependency
from gaiafaac_api.pipeline.analytics.forecasting import compute_forecasts
from gaiafaac_api.pipeline.analytics.rankings import compute_rankings
from gaiafaac_api.pipeline.analytics.volatility import compute_volatility


@dataclass(frozen=True)
class AnalyticsRunResult:
    indicators: int
    forecasts: int


def compute_analytics(session: Session) -> AnalyticsRunResult:
    """Recompute and persist all analytics for the demo dataset (idempotent)."""
    source = analytics_source(session)
    if source is None:
        return AnalyticsRunResult(0, 0)

    session.execute(delete(StateIndicator).where(StateIndicator.source_document_id == source.id))
    session.execute(delete(Forecast).where(Forecast.source_document_id == source.id))

    indicator_specs = (
        compute_rankings(session) + compute_volatility(session) + compute_dependency(session)
    )
    for spec in indicator_specs:
        session.add(
            StateIndicator(
                reporting_period_id=spec.reporting_period_id,
                state_id=spec.state_id,
                source_document_id=spec.source_document_id,
                indicator_type=spec.indicator_type,
                indicator_name=spec.indicator_name,
                value=spec.value,
                unit=spec.unit,
                methodology=spec.methodology,
                verification_status=VerificationStatus.PENDING,
            )
        )

    forecast_specs = compute_forecasts(session)
    for spec in forecast_specs:
        session.add(
            Forecast(
                state_id=spec.state_id,
                source_document_id=spec.source_document_id,
                target_period=spec.target_period,
                method=spec.method,
                point_estimate=spec.point_estimate,
                lower_bound=spec.lower_bound,
                upper_bound=spec.upper_bound,
                training_start=spec.training_start,
                training_end=spec.training_end,
                metrics=spec.metrics,
                verification_status=VerificationStatus.PENDING,
                is_demo=True,
                is_published=False,
            )
        )

    session.commit()
    return AnalyticsRunResult(len(indicator_specs), len(forecast_specs))
```

- [ ] **Step 4: Apply the test note, then run tests**

Simplify the `StateIndicator` assertion as noted in Step 1, then run:
`python -m pytest apps/api/tests/test_analytics_run.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/analytics/run.py apps/api/tests/test_analytics_run.py
git commit -m "feat(analytics): persist analytics idempotently via orchestrator"
```

---

## Task 8: Read schemas and services

**Files:**
- Create: `apps/api/src/gaiafaac_api/analytics_schemas.py`
- Create: `apps/api/src/gaiafaac_api/services/analytics.py`
- Test: `apps/api/tests/test_analytics_service.py`

**Interfaces:**
- Consumes: models `State`, `StateIndicator`, `Forecast`; `common.latest_analytics_period`, `analytics_source`, `DEMO_DATA_LABEL`.
- Produces schemas: `RankingsResponse`, `VolatilityResponse`, `DependencyResponse`, `ForecastsResponse` (each with `data_label: Literal["DEMO DATA - NOT REAL FAAC DATA"]`).
- Produces services: `get_rankings(session) -> RankingsResponse | None`, `get_volatility(session) -> VolatilityResponse | None`, `get_dependency(session) -> DependencyResponse | None`, `get_forecasts(session) -> ForecastsResponse | None` (None when no analytics data).

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_service.py
from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics
from gaiafaac_api.services.analytics import (
    get_dependency,
    get_forecasts,
    get_rankings,
    get_volatility,
)

LABEL = "DEMO DATA - NOT REAL FAAC DATA"


def _prepare(session: Session) -> None:
    generate_analytics_dataset(session)
    compute_analytics(session)


def test_services_return_labelled_data(session: Session) -> None:
    assert get_rankings(session) is None  # nothing computed yet
    _prepare(session)

    rankings = get_rankings(session)
    assert rankings is not None
    assert rankings.data_label == LABEL
    assert len(rankings.rankings) == 37
    assert rankings.rankings[0].rank == 1

    volatility = get_volatility(session)
    assert volatility is not None and len(volatility.rows) == 37

    dependency = get_dependency(session)
    assert dependency is not None and len(dependency.rows) == 37
    assert all(row.concentration_hhi is not None for row in dependency.rows)

    forecasts = get_forecasts(session)
    assert forecasts is not None and len(forecasts.forecasts) == 37
    assert all(f.is_estimate is True for f in forecasts.forecasts)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_service.py -v`
Expected: FAIL with `ModuleNotFoundError: ...services.analytics`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/analytics_schemas.py
from datetime import date
from typing import Literal

from pydantic import BaseModel

DEMO_DATA_LABEL = "DEMO DATA - NOT REAL FAAC DATA"
_LABEL = Literal["DEMO DATA - NOT REAL FAAC DATA"]


class RankingRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    geopolitical_zone: str
    net_allocation: str | None
    rank: int
    rank_change: int | None


class RankingsResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    reporting_label: str
    revenue_month: date
    rankings: list[RankingRow]


class VolatilityRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    coefficient_of_variation: str


class VolatilityResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    window_periods: int
    rows: list[VolatilityRow]


class DependencyRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    shares: dict[str, str]
    concentration_hhi: str | None


class DependencyResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    reporting_label: str
    rows: list[DependencyRow]


class ForecastRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    method: str
    target_period: date
    point_estimate: str
    lower_bound: str
    upper_bound: str
    training_start: date
    training_end: date
    is_estimate: Literal[True] = True


class ForecastsResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    forecasts: list[ForecastRow]
```

```python
# apps/api/src/gaiafaac_api/services/analytics.py
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.analytics_schemas import (
    DependencyResponse,
    DependencyRow,
    ForecastRow,
    ForecastsResponse,
    RankingRow,
    RankingsResponse,
    VolatilityResponse,
    VolatilityRow,
)
from gaiafaac_api.database.models import Forecast, State, StateAllocation, StateIndicator
from gaiafaac_api.pipeline.analytics.common import (
    VOLATILITY_WINDOW,
    analytics_source,
    latest_analytics_period,
)

_SCOPE = (
    "Synthetic demo analytics computed from labelled demo figures only. "
    "Not real FAAC data; forecasts are estimates, not reported allocations."
)


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _ratio(value: Decimal | None) -> str | None:
    return format(value, "f") if value is not None else None


def _states(session: Session) -> dict:
    return {state.id: state for state in session.scalars(select(State))}


def get_rankings(session: Session) -> RankingsResponse | None:
    latest = latest_analytics_period(session)
    if latest is None:
        return None
    indicators = list(
        session.scalars(
            select(StateIndicator).where(
                StateIndicator.reporting_period_id == latest.id,
                StateIndicator.indicator_type == "ranking",
            )
        )
    )
    if not indicators:
        return None
    states = _states(session)
    nets = {
        state_id: net
        for state_id, net in session.execute(
            select(StateAllocation.state_id, StateAllocation.net_allocation).where(
                StateAllocation.reporting_period_id == latest.id
            )
        )
    }
    ranks = {i.state_id: int(i.value) for i in indicators if i.indicator_name == "net_allocation_rank"}
    changes = {
        i.state_id: int(i.value)
        for i in indicators
        if i.indicator_name == "net_allocation_rank_change"
    }
    rows = [
        RankingRow(
            state_name=states[state_id].name,
            state_code=states[state_id].code,
            state_slug=states[state_id].slug,
            geopolitical_zone=states[state_id].geopolitical_zone,
            net_allocation=_money(nets.get(state_id)),
            rank=rank,
            rank_change=changes.get(state_id),
        )
        for state_id, rank in sorted(ranks.items(), key=lambda kv: kv[1])
    ]
    return RankingsResponse(
        scope_note=_SCOPE,
        reporting_label=latest.reporting_label,
        revenue_month=latest.revenue_month,
        rankings=rows,
    )


def get_volatility(session: Session) -> VolatilityResponse | None:
    latest = latest_analytics_period(session)
    if latest is None:
        return None
    indicators = list(
        session.scalars(
            select(StateIndicator).where(
                StateIndicator.reporting_period_id == latest.id,
                StateIndicator.indicator_type == "volatility",
            )
        )
    )
    if not indicators:
        return None
    states = _states(session)
    rows = [
        VolatilityRow(
            state_name=states[i.state_id].name,
            state_code=states[i.state_id].code,
            state_slug=states[i.state_id].slug,
            coefficient_of_variation=_ratio(i.value),
        )
        for i in sorted(indicators, key=lambda i: states[i.state_id].name)
    ]
    return VolatilityResponse(scope_note=_SCOPE, window_periods=VOLATILITY_WINDOW, rows=rows)


def get_dependency(session: Session) -> DependencyResponse | None:
    latest = latest_analytics_period(session)
    if latest is None:
        return None
    indicators = list(
        session.scalars(
            select(StateIndicator).where(
                StateIndicator.reporting_period_id == latest.id,
                StateIndicator.indicator_type == "dependency",
            )
        )
    )
    if not indicators:
        return None
    states = _states(session)
    shares: dict = {}
    hhi: dict = {}
    for indicator in indicators:
        if indicator.indicator_name == "net_concentration_hhi":
            hhi[indicator.state_id] = indicator.value
        elif indicator.indicator_name.endswith("_net_share"):
            component = indicator.indicator_name.removesuffix("_net_share")
            shares.setdefault(indicator.state_id, {})[component] = _ratio(indicator.value)
    rows = [
        DependencyRow(
            state_name=states[state_id].name,
            state_code=states[state_id].code,
            state_slug=states[state_id].slug,
            shares=shares.get(state_id, {}),
            concentration_hhi=_ratio(hhi.get(state_id)),
        )
        for state_id in sorted(hhi, key=lambda sid: states[sid].name)
    ]
    return DependencyResponse(scope_note=_SCOPE, reporting_label=latest.reporting_label, rows=rows)


def get_forecasts(session: Session) -> ForecastsResponse | None:
    source = analytics_source(session)
    if source is None:
        return None
    forecasts = list(
        session.scalars(
            select(Forecast).where(
                Forecast.source_document_id == source.id,
                Forecast.is_demo.is_(True),
                Forecast.is_published.is_(False),
            )
        )
    )
    if not forecasts:
        return None
    states = _states(session)
    rows = [
        ForecastRow(
            state_name=states[f.state_id].name,
            state_code=states[f.state_id].code,
            state_slug=states[f.state_id].slug,
            method=f.method.value,
            target_period=f.target_period,
            point_estimate=_money(f.point_estimate),
            lower_bound=_money(f.lower_bound),
            upper_bound=_money(f.upper_bound),
            training_start=f.training_start,
            training_end=f.training_end,
        )
        for f in sorted(forecasts, key=lambda f: states[f.state_id].name)
    ]
    return ForecastsResponse(scope_note=_SCOPE, forecasts=rows)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_analytics_service.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/analytics_schemas.py apps/api/src/gaiafaac_api/services/analytics.py apps/api/tests/test_analytics_service.py
git commit -m "feat(analytics): add read schemas and demo-constrained services"
```

---

## Task 9: API routes

**Files:**
- Create: `apps/api/src/gaiafaac_api/api/v1/routes/analytics.py`
- Modify: `apps/api/src/gaiafaac_api/api/v1/router.py`
- Test: `apps/api/tests/test_analytics_api.py`

**Interfaces:**
- Consumes: services from Task 8; `get_session`.
- Produces: router with `GET /analytics/rankings`, `/analytics/volatility`, `/analytics/dependency`, `/analytics/forecasts`; each 404s when no analytics data.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_api.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.analytics import forecasts, rankings
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics


def test_rankings_route_404_without_data(session: Session) -> None:
    with pytest.raises(HTTPException) as error:
        rankings(session)
    assert error.value.status_code == 404


def test_routes_return_labelled_payloads(session: Session) -> None:
    generate_analytics_dataset(session)
    compute_analytics(session)

    payload = rankings(session)
    assert payload.data_label == "DEMO DATA - NOT REAL FAAC DATA"
    assert len(payload.rankings) == 37

    forecast_payload = forecasts(session)
    assert all(f.is_estimate is True for f in forecast_payload.forecasts)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_api.py -v`
Expected: FAIL with `ModuleNotFoundError: ...routes.analytics`.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/api/v1/routes/analytics.py
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.analytics_schemas import (
    DependencyResponse,
    ForecastsResponse,
    RankingsResponse,
    VolatilityResponse,
)
from gaiafaac_api.database.session import get_session
from gaiafaac_api.services.analytics import (
    get_dependency,
    get_forecasts,
    get_rankings,
    get_volatility,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
DatabaseSession = Annotated[Session, Depends(get_session)]

_NOT_FOUND = "No labelled demo analytics are available. Run compute-analytics first."


@router.get("/rankings", response_model=RankingsResponse, summary="Demo net-allocation rankings")
def rankings(session: DatabaseSession) -> RankingsResponse:
    result = get_rankings(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result


@router.get("/volatility", response_model=VolatilityResponse, summary="Demo volatility")
def volatility(session: DatabaseSession) -> VolatilityResponse:
    result = get_volatility(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result


@router.get("/dependency", response_model=DependencyResponse, summary="Demo revenue dependency")
def dependency(session: DatabaseSession) -> DependencyResponse:
    result = get_dependency(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result


@router.get("/forecasts", response_model=ForecastsResponse, summary="Demo forecasts (estimates)")
def forecasts(session: DatabaseSession) -> ForecastsResponse:
    result = get_forecasts(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result
```

Modify `apps/api/src/gaiafaac_api/api/v1/router.py` to include the router:

```python
from fastapi import APIRouter

from gaiafaac_api.api.v1.routes.analytics import router as analytics_router
from gaiafaac_api.api.v1.routes.demo_data import router as demo_data_router
from gaiafaac_api.api.v1.routes.health import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(demo_data_router)
router.include_router(analytics_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_analytics_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/api/v1/routes/analytics.py apps/api/src/gaiafaac_api/api/v1/router.py apps/api/tests/test_analytics_api.py
git commit -m "feat(analytics): expose demo-constrained analytics read endpoints"
```

---

## Task 10: CLI wiring

**Files:**
- Modify: `apps/api/src/gaiafaac_api/cli.py`
- Test: `apps/api/tests/test_analytics_cli.py`

**Interfaces:**
- Consumes: `generate_analytics_dataset`, `compute_analytics`, `build_parser`.
- Produces: CLI verbs `seed-analytics-demo` and `compute-analytics`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_analytics_cli.py
from gaiafaac_api.cli import build_parser


def test_parser_accepts_analytics_commands() -> None:
    parser = build_parser()
    assert parser.parse_args(["seed-analytics-demo"]).command == "seed-analytics-demo"
    assert parser.parse_args(["compute-analytics"]).command == "compute-analytics"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_analytics_cli.py -v`
Expected: FAIL (`invalid choice: 'seed-analytics-demo'`).

- [ ] **Step 3: Write minimal implementation**

In `apps/api/src/gaiafaac_api/cli.py`, add imports near the top:
```python
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics
```

In `build_parser()`, before `return parser`, register the subcommands:
```python
    commands.add_parser("seed-analytics-demo", help="Generate the synthetic analytics demo dataset")
    commands.add_parser("compute-analytics", help="Compute and persist demo analytics")
```

In `main()`, add dispatch branches alongside the others:
```python
        elif args.command == "seed-analytics-demo":
            summary = generate_analytics_dataset(session)
            print(
                f"Analytics dataset ready: periods={summary.periods}, "
                f"allocations={summary.allocations}, components={summary.components}."
            )
        elif args.command == "compute-analytics":
            result = compute_analytics(session)
            print(
                f"Analytics computed: indicators={result.indicators}, "
                f"forecasts={result.forecasts}."
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_analytics_cli.py -v`
Expected: PASS.

- [ ] **Step 5: Full suite + lint, then commit**

```bash
python -m ruff format apps/api
python -m ruff check apps/api
python -m pytest apps/api/tests -q
git add apps/api/src/gaiafaac_api/cli.py apps/api/tests/test_analytics_cli.py
git commit -m "feat(analytics): add seed-analytics-demo and compute-analytics CLI verbs"
```
Expected: ruff clean; full suite passes (existing M4 tests + all new analytics tests).

---

## Self-Review (completed by plan author)

**Spec coverage:** dataset generator (Task 2), rankings/volatility/dependency/forecasting (Tasks 3–6), storage+idempotence (Task 7), read API (Tasks 8–9), CLI (Task 10), fail-closed omission (helpers in Tasks 4–6 return `None`), no new migration (uses existing `state_indicators`/`forecasts`), M4 non-regression (Task 2 test). All spec sections map to a task.

**Placeholder scan:** the two "Note" callouts (Task 1 stats assertion, Task 7 `StateIndicator.is_demo`) are corrected within their own Step 4 before the task completes — no placeholders remain in shipped code.

**Type consistency:** `IndicatorSpec`/`ForecastSpec` defined once in `common.py` and consumed unchanged in Tasks 3–8; `analytics_source`/`analytics_periods`/`latest_analytics_period` signatures stable across tasks; service/schema names (`RankingsResponse.rankings`, `DependencyRow.concentration_hhi`, `ForecastRow.is_estimate`) match between Tasks 8 and 9 tests.

## Known follow-ups (out of scope for this plan)

- Cycle 1b: shared TS types, Zod schemas, and server-rendered analytics pages with accessible charts.
- Sub-project 2 (reports) and sub-project 3 (grounded Ask Gaia) — separate specs/plans.
