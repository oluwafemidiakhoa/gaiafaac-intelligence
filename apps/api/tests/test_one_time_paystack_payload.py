from __future__ import annotations

import json
from types import SimpleNamespace

from gaiafaac_api.api.v1.routes import one_time_billing


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(
            {
                "status": True,
                "data": {"authorization_url": "https://checkout.paystack.com/test"},
            }
        ).encode("utf-8")


def test_one_time_paystack_initialize_uses_provider_contract(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        one_time_billing,
        "get_settings",
        lambda: SimpleNamespace(
            paystack_secret_key="sk_test_example",
            customer_app_url="https://gaia.example",
        ),
    )

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setattr(one_time_billing, "urlopen", fake_urlopen)

    url = one_time_billing._initialize_paystack_transaction(
        email="buyer@example.com",
        reference="gfi-order-abc123",
        amount_naira=50_000,
        metadata={
            "purchase_mode": "one_time",
            "purchase_id": "11111111-2222-4333-8444-555555555555",
        },
    )

    assert url == "https://checkout.paystack.com/test"
    assert captured["timeout"] == 12

    request = captured["request"]
    payload = json.loads(request.data.decode("utf-8"))

    # Paystack's initialize contract requires amount and metadata as strings.
    assert payload["amount"] == "5000000"
    assert isinstance(payload["amount"], str)
    assert isinstance(payload["metadata"], str)
    assert json.loads(payload["metadata"]) == {
        "purchase_mode": "one_time",
        "purchase_id": "11111111-2222-4333-8444-555555555555",
    }
    assert payload["callback_url"] == (
        "https://gaia.example/projects?purchase=return&reference=gfi-order-abc123"
    )
    assert request.headers["Authorization"] == "Bearer sk_test_example"
    assert request.headers["Content-type"] == "application/json"
    assert request.headers["Accept"] == "application/json"
    assert request.headers["User-agent"] == "GaiaFiscalIntelligence/1.0"
