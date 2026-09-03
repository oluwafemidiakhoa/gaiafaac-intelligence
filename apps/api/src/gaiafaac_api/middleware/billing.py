"""Middleware for billing and usage tracking"""

from collections.abc import Callable

from fastapi import Request
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from gaiafaac_api.database.subscription_models import OrganizationSubscription
from gaiafaac_api.services.billing import BillingService


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Track API usage for billing purposes"""

    def __init__(self, app, session_factory: sessionmaker):
        super().__init__(app)
        self.session_factory = session_factory

    async def dispatch(self, request: Request, call_next: Callable) -> StreamingResponse:
        """Log usage on each request"""
        response = await call_next(request)

        try:
            organization_id = request.headers.get("X-Organization-ID")
            if organization_id:
                with self.session_factory() as session:
                    subscription = (
                        session.query(OrganizationSubscription)
                        .filter_by(organization_id=organization_id)
                        .first()
                    )

                    if subscription:
                        billing_service = BillingService(session)
                        billing_service.log_usage(
                            organization_id=subscription.organization_id,
                            subscription_id=subscription.id,
                            event_type="api_call",
                            endpoint=request.url.path,
                            method=request.method,
                            response_status=response.status_code,
                            user_id=request.headers.get("X-User-ID"),
                        )
        except Exception:
            pass

        return response
