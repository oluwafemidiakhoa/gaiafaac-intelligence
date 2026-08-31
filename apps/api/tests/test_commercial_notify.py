import smtplib

from gaiafaac_api.config import Settings
from gaiafaac_api.database.commercial_models import PilotLead
from gaiafaac_api.services.commercial_notify import send_pilot_lead_alert


def _settings(**over):
    base = dict(
        smtp_host="smtp.zoho.com",
        smtp_port=465,
        smtp_username="alerts@example.com",
        smtp_password="app-pw",
        alert_from="alerts@example.com",
        alert_to="sales@example.com",
        customer_app_url="https://app.example.com",
    )
    base.update(over)
    return Settings(**base)


def _lead(**over) -> PilotLead:
    base = dict(
        name="Ada Analyst",
        email="ada@example.com",
        organization="Civic Research Lab",
        role="Researcher",
        country="Nigeria",
        plan_interest="api",
        use_case="We need governed FAAC evidence for a fixed-income desk.",
        states_or_periods="Edo, Delta; 2024",
        preferred_format="json",
        expected_users=5,
    )
    base.update(over)
    return PilotLead(**base)


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
    ok = send_pilot_lead_alert(_settings(), lead=_lead())
    assert ok is True
    sent = _FakeSMTP.sent[0]
    assert "Civic Research Lab" in sent["Subject"]
    assert "https://app.example.com/admin/leads" in sent.get_content()


def test_skips_when_unconfigured(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("must not connect")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _boom)
    assert send_pilot_lead_alert(_settings(smtp_password=""), lead=_lead()) is False


def test_swallows_smtp_errors(monkeypatch):
    class _Broken(_FakeSMTP):
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"bad")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _Broken)
    assert send_pilot_lead_alert(_settings(), lead=_lead()) is False
