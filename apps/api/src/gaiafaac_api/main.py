from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from gaiafaac_api.api.v1.router import router as api_v1_router
from gaiafaac_api.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Gaia Fiscal Intelligence API",
        summary="Verified public-finance data, evidence and fiscal events for Nigeria",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Accept", "Content-Type"],
    )

    # API-key request accounting is performed by the canonical API-key service.
    # The older X-Organization-ID usage middleware is intentionally not mounted:
    # it trusted caller-supplied organization headers and wrote to a legacy
    # subscription generation that is no longer authoritative for entitlements.
    application.include_router(api_v1_router)

    @application.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return application


app = create_app()
