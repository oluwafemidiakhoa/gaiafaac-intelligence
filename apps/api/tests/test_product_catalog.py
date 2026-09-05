from gaiafaac_api.database.enums import PlanCode
from gaiafaac_api.services.product_catalog import (
    PRODUCT_CATALOG,
    ProductBillingMode,
    product_by_code,
    public_product_catalog,
)


def test_product_catalog_supports_all_required_billing_modes() -> None:
    modes = {product.billing_mode for product in PRODUCT_CATALOG}
    assert {
        ProductBillingMode.SUBSCRIPTION,
        ProductBillingMode.ONE_TIME,
        ProductBillingMode.ENTERPRISE_QUOTE,
        ProductBillingMode.USAGE,
    } <= modes


def test_unapproved_transactional_and_enterprise_prices_are_not_invented() -> None:
    for product in PRODUCT_CATALOG:
        if product.billing_mode in {
            ProductBillingMode.ONE_TIME,
            ProductBillingMode.ENTERPRISE_QUOTE,
        }:
            assert product.price_usd is None
            assert product.price_naira is None


def test_subscription_catalog_is_tied_to_canonical_plan_codes() -> None:
    analyst = product_by_code("subscription_analyst")
    team = product_by_code("subscription_team")
    api = product_by_code("subscription_api")

    assert analyst is not None and analyst.plan_code == PlanCode.ANALYST.value
    assert team is not None and team.plan_code == PlanCode.TEAM.value
    assert api is not None and api.plan_code == PlanCode.API.value


def test_public_catalog_is_serializable_configuration() -> None:
    catalog = public_product_catalog()
    assert catalog
    assert any(item["code"] == "decision_pack" for item in catalog)
    assert any(item["code"] == "enterprise_data_feed" for item in catalog)
