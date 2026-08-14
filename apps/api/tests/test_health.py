import asyncio

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from gaiafaac_api.config import get_settings
from gaiafaac_api.main import app, create_app


async def get(application: FastAPI, path: str):
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


def test_health_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_ENVIRONMENT", "test")
    get_settings.cache_clear()

    response = asyncio.run(get(create_app(), "/api/v1/health"))

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "gaiafaac-api",
        "version": "0.1.0",
        "environment": "test",
    }
    get_settings.cache_clear()


def test_openapi_exposes_versioned_health_endpoint() -> None:
    schema = asyncio.run(get(app, "/api/v1/openapi.json")).json()

    assert "/api/v1/health" in schema["paths"]
    assert {
        "/api/v1/overview/latest",
        "/api/v1/states",
        "/api/v1/states/{slug}",
        "/api/v1/compare",
        "/api/v1/sources",
        "/api/v1/jurisdictions/{code}/state",
        "/api/v1/jurisdictions/{code}/evidence",
        "/api/v1/evidence-sources",
        "/api/v1/proofs/{gaia_id}",
        "/api/v1/events",
        "/api/v1/jurisdictions/{code}/events",
        "/api/v1/certificates/{gaia_id}",
        "/api/v1/fiscal-states/{gaia_id}",
        "/api/v1/verify",
    } <= set(schema["paths"])
