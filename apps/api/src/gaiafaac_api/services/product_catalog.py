from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import StrEnum

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.enums import PlanCode
from gaiafaac_api.entitlements import PLAN_ENTITLEMENTS


class ProductBillingMode(StrEnum):
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"
    ENTERPRISE_QUOTE = "enterprise_quote"
    USAGE = "usage"


@dataclass(frozen=True)
class CommercialProduct:
    code: str
    label: str
    billing_mode: ProductBillingMode
    description: str
    plan_code: str | None = None
    price_usd: int | None = None
    price_naira: int | None = None
    quote_required: bool = False

    def public_dict(self) -> dict:
        return asdict(self)


def _subscription_product(plan_code: PlanCode, description: str) -> CommercialProduct:
    entitlement = PLAN_ENTITLEMENTS[plan_code]
    return CommercialProduct(
        code=f"subscription_{plan_code.value}",
        label=entitlement.label,
        billing_mode=ProductBillingMode.SUBSCRIPTION,
        description=description,
        plan_code=plan_code.value,
        price_usd=entitlement.price_usd_monthly,
    )


PRODUCT_CATALOG: tuple[CommercialProduct, ...] = (
    CommercialProduct(
        code="public",
        label="Public",
        billing_mode=ProductBillingMode.USAGE,
        description="Latest public governed evidence and verification surfaces.",
        plan_code=PlanCode.FREE.value,
        price_usd=0,
    ),
    _subscription_product(
        PlanCode.ANALYST,
        "Historical evidence, exports, saved research, Decision Room and receipt workflows within Analyst entitlements.",
    ),
    _subscription_product(
        PlanCode.TEAM,
        "Shared organization research, Decision Rooms, monitoring and reviewer workflows within Team entitlements.",
    ),
    _subscription_product(
        PlanCode.API,
        "Programmatic governed evidence, receipt verification, revision-aware integration and API entitlements.",
    ),
    CommercialProduct(
        code="decision_pack",
        label="Individual Decision Pack",
        billing_mode=ProductBillingMode.ONE_TIME,
        description="One jurisdiction and a defined governed evidence period packaged for a specific decision review.",
    ),
    CommercialProduct(
        code="multi_state_comparison_pack",
        label="Multi-State Comparison Pack",
        billing_mode=ProductBillingMode.ONE_TIME,
        description="A governed comparison across selected jurisdictions and a declared evidence period.",
    ),
    CommercialProduct(
        code="historical_evidence_export",
        label="Historical Fiscal Evidence Export",
        billing_mode=ProductBillingMode.ONE_TIME,
        description="A provenance-preserving historical evidence export where the requested governed lane is available.",
    ),
    CommercialProduct(
        code="due_diligence_snapshot",
        label="Due-Diligence Evidence Snapshot",
        billing_mode=ProductBillingMode.ONE_TIME,
        description="A frozen, verifiable evidence boundary for a defined due-diligence review.",
    ),
    CommercialProduct(
        code="custom_watch_setup",
        label="Custom Fiscal Watch Setup",
        billing_mode=ProductBillingMode.ENTERPRISE_QUOTE,
        description="A customer-defined monitoring mandate over supported governed evidence lanes.",
        quote_required=True,
    ),
    CommercialProduct(
        code="institutional_research_pack",
        label="Institutional Research Pack",
        billing_mode=ProductBillingMode.ENTERPRISE_QUOTE,
        description="A scoped institutional evidence and decision-workflow engagement.",
        quote_required=True,
    ),
    CommercialProduct(
        code="enterprise_data_feed",
        label="Enterprise API / Data Feed",
        billing_mode=ProductBillingMode.ENTERPRISE_QUOTE,
        description="Governed evidence integration, monitoring and permitted downstream rights subject to contract.",
        quote_required=True,
    ),
)


def _configured_product(product: CommercialProduct) -> CommercialProduct:
    if product.billing_mode != ProductBillingMode.ONE_TIME:
        return product
    settings = get_settings()
    prices = {
        "decision_pack": settings.paystack_price_decision_pack,
        "multi_state_comparison_pack": settings.paystack_price_multi_state_comparison_pack,
        "historical_evidence_export": settings.paystack_price_historical_evidence_export,
        "due_diligence_snapshot": settings.paystack_price_due_diligence_snapshot,
    }
    configured_price = prices.get(product.code, 0)
    return replace(product, price_naira=configured_price or None)


def product_by_code(code: str) -> CommercialProduct | None:
    normalized = code.strip().lower()
    product = next((item for item in PRODUCT_CATALOG if item.code == normalized), None)
    return _configured_product(product) if product is not None else None


def public_product_catalog() -> list[dict]:
    """Return only approved/configured prices; zero-valued one-time prices stay unavailable."""
    return [_configured_product(product).public_dict() for product in PRODUCT_CATALOG]
