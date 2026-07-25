from fastapi import APIRouter

from gaiafaac_api.config import get_settings
from gaiafaac_api.schemas import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Check API liveness")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="gaiafaac-api",
        version="0.1.0",
        environment=settings.api_environment,
    )
