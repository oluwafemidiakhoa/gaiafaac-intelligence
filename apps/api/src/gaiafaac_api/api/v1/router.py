from fastapi import APIRouter

from gaiafaac_api.api.v1.routes.account import router as account_router
from gaiafaac_api.api.v1.routes.analytics import router as analytics_router
from gaiafaac_api.api.v1.routes.billing import router as billing_router
from gaiafaac_api.api.v1.routes.billing_dashboard import router as billing_dashboard_router
from gaiafaac_api.api.v1.routes.commercial import router as commercial_router
from gaiafaac_api.api.v1.routes.data_api import router as data_api_router
from gaiafaac_api.api.v1.routes.decision_reviews import router as decision_reviews_router
from gaiafaac_api.api.v1.routes.demo_data import router as demo_data_router
from gaiafaac_api.api.v1.routes.dmo_review import router as dmo_review_router
from gaiafaac_api.api.v1.routes.evidence_provenance import router as evidence_provenance_router
from gaiafaac_api.api.v1.routes.evidence_rooms import router as evidence_rooms_router
from gaiafaac_api.api.v1.routes.fiscal_claims import router as fiscal_claims_router
from gaiafaac_api.api.v1.routes.fiscal_design_decision_rooms import (
    router as fiscal_design_decision_rooms_router,
)
from gaiafaac_api.api.v1.routes.fiscal_ledger import router as fiscal_ledger_router
from gaiafaac_api.api.v1.routes.fiscal_receipts import router as fiscal_receipts_router
from gaiafaac_api.api.v1.routes.health import router as health_router
from gaiafaac_api.api.v1.routes.institutional_audit import router as institutional_audit_router
from gaiafaac_api.api.v1.routes.institutional_decisions import (
    router as institutional_decisions_router,
)
from gaiafaac_api.api.v1.routes.institutional_webhooks import router as webhook_router
from gaiafaac_api.api.v1.routes.lga_status import router as lga_status_router
from gaiafaac_api.api.v1.routes.national_distribution import (
    router as national_distribution_router,
)
from gaiafaac_api.api.v1.routes.national_review import router as national_review_router
from gaiafaac_api.api.v1.routes.nbs_igr_review import router as nbs_igr_review_router
from gaiafaac_api.api.v1.routes.oagf_revisions import router as oagf_revisions_router
from gaiafaac_api.api.v1.routes.one_time_billing import router as one_time_billing_router
from gaiafaac_api.api.v1.routes.published_data import router as published_data_router
from gaiafaac_api.api.v1.routes.review import router as review_router
from gaiafaac_api.api.v1.routes.temporal import router as temporal_router
from gaiafaac_api.api.v1.routes.watch_contracts import router as watch_contracts_router
from gaiafaac_api.api.v1.routes.watchlists import router as watchlists_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(fiscal_ledger_router)
router.include_router(fiscal_claims_router)
router.include_router(temporal_router)
router.include_router(demo_data_router)
router.include_router(analytics_router)
router.include_router(published_data_router)
router.include_router(lga_status_router)
router.include_router(national_distribution_router)
router.include_router(data_api_router)
router.include_router(commercial_router)
router.include_router(account_router)
router.include_router(billing_router)
router.include_router(one_time_billing_router)
router.include_router(billing_dashboard_router)
router.include_router(watchlists_router)
router.include_router(watch_contracts_router)
router.include_router(evidence_provenance_router)
router.include_router(evidence_rooms_router)
router.include_router(fiscal_design_decision_rooms_router)
router.include_router(decision_reviews_router)
router.include_router(fiscal_receipts_router)
router.include_router(institutional_audit_router)
router.include_router(institutional_decisions_router)
router.include_router(webhook_router)
router.include_router(national_review_router)
router.include_router(oagf_revisions_router)
router.include_router(review_router)
router.include_router(dmo_review_router)
router.include_router(nbs_igr_review_router)
