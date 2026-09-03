import hashlib
import hmac

from gaiafaac_api.api.v1.routes.billing import _verify_paystack_webhook


def test_paystack_webhook_uses_hmac_sha512():
    secret = "sk_test_example"
    payload = b'{"event":"charge.success","data":{"reference":"gfi-test"}}'
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha512).hexdigest()

    assert _verify_paystack_webhook(signature, payload, secret)


def test_paystack_webhook_rejects_modified_payload():
    secret = "sk_test_example"
    payload = b'{"event":"charge.success"}'
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha512).hexdigest()

    assert not _verify_paystack_webhook(signature, payload + b" ", secret)
