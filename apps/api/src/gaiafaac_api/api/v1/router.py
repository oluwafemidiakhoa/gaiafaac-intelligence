from fastapi import APIRouter

from gaiafaac_api.api.v1.routes.account import router as account_router
from gaiafaac_api.api.v1.routes.analytics import router as analytics_router
from gaiafaac_api.api.v1.routes.billing import router as billing_router
from gaiafaac_api.api.v1.routes.commercial import router as commercial_router
from gaiafaac_api.api.v1.routes.data_api import router as data_api_router
from gaiafaac_api.api.v1.routes.demo_data import router as demo_data_router
from gaiafaac_api.api.v1.routes.evidence_rooms import router as evidence_rooms_router
from gaiafaac_api.api.v1.routes.fiscal_claims import router as fiscal_claims_router
from gaiafaac_api.api.v1.routes.fiscal_ledger import router as fiscal_ledger_router
from gaiafaac_api.api.v1.routes.health import router as health_router
from gaiafaac_api.api.v1.routes.institutional_webhooks import router as webhook_router
from gaiafaac_api.api.v1.routes.national_distribution import (
    router as national_distribution_router,
)
from gaiafaac_api.api.v1.routes.national_review import router as national_review_router
from gaiafaac_api.api.v1.routes.oagf_revisions import router as oagf_revisions_router
from gaiafaac_api.api.v1.routes.published_data import router as published_data_router
from gaiafaac_api.api.v1.routes.review import router as review_router
from gaiafaac_api.api.v1.routes.temporal import router as temporal_router
from gaiafaac_api.api.v1.routes.watchlists import router as watchlists_router

router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(fiscal_ledger_router)
router.include_router(fiscal_claims_router)
router.include_router(temporal_router)
router.include_router(demo_data_router)
router.include_router(analytics_router)
router.include_router(published_data_router)
router.include_router(national_distribution_router)
router.include_router(data_api_router)
router.include_router(commercial_router)
router.include_router(account_router)
router.include_router(billing_router)
router.include_router(watchlists_router)
router.include_router(evidence_rooms_router)
router.include_router(webhook_router)
router.include_router(national_review_router)
router.include_router(oagf_revisions_router)
router.include_router(review_router)
