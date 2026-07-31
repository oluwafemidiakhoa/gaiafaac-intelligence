import smtplib

from gaiafaac_api.config import Settings
from gaiafaac_api.pipeline.collection.notify import send_review_alert


def _settings(**over):
    base = dict(
        smtp_host="smtp.zoho.com",
        smtp_port=465,
        smtp_username="alerts@example.com",
        smtp_password="app-pw",
        alert_from="alerts@example.com",
        alert_to="me@example.com",
    )
    base.update(over)
    return Settings(**base)


class _FakeSMTP:
    sent: list = []

    def __init__(self, host, port):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, user, password):
        pass

    def send_message(self, message):
        _FakeSMTP.sent.append(message)


def test_sends_when_configured(monkeypatch):
    _FakeSMTP.sent = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", _FakeSMTP)
    ok = send_review_alert(
        _settings(),
        reporting_label="OAGF Jan 2024",
        records_extracted=36,
        blocking_finding_count=2,
        queue_url="https://x/review/pending",
    )
    assert ok is True
    assert "OAGF Jan 2024" in _FakeSMTP.sent[0]["Subject"]


def test_skips_when_unconfigured(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("must not connect")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _boom)
    assert (
        send_review_alert(
            _settings(smtp_password=""),
            reporting_label="X",
            records_extracted=1,
            blocking_finding_count=0,
            queue_url="https://x",
        )
        is False
    )


def test_swallows_smtp_errors(monkeypatch):
    class _Broken(_FakeSMTP):
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"bad")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _Broken)
    assert (
        send_review_alert(
            _settings(),
            reporting_label="X",
            records_extracted=1,
            blocking_finding_count=0,
            queue_url="https://x",
        )
        is False
    )
