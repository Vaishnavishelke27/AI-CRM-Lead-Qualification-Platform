import asyncio
import smtplib
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.database import SessionLocal
from app.models import Lead, ReportingSchedule, Task
from services import reporting_service


SUMMARY = {
    "generated_at": "2026-07-17T12:00:00+00:00",
    "total_leads": 10,
    "hot_leads": 3,
    "conversion_rate": 20.0,
    "open_tasks": 4,
}


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.starttls_called = False
        self.login_args = None
        self.message = None
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def ehlo(self):
        return None

    def starttls(self):
        self.starttls_called = True

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, message):
        self.message = message


def configure_smtp(monkeypatch):
    monkeypatch.setattr(settings, "reporting_email_to", "manager@example.com")
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "smtp-user")
    monkeypatch.setattr(settings, "smtp_password", "smtp-password")
    monkeypatch.setattr(settings, "smtp_from_email", "crm@example.com")
    monkeypatch.setattr(settings, "smtp_starttls", True)


def test_send_summary_delivers_through_smtp(monkeypatch):
    configure_smtp(monkeypatch)
    FakeSMTP.instances.clear()
    monkeypatch.setattr(reporting_service.smtplib, "SMTP", FakeSMTP)

    result = asyncio.run(reporting_service.send_summary(SUMMARY))

    assert result["sent"] is True
    smtp = FakeSMTP.instances[0]
    assert (smtp.host, smtp.port, smtp.timeout) == ("smtp.example.com", 587, 15)
    assert smtp.starttls_called
    assert smtp.login_args == ("smtp-user", "smtp-password")
    assert smtp.message["From"] == "crm@example.com"
    assert smtp.message["To"] == "manager@example.com"
    assert "Total leads: 10" in smtp.message.get_content()


def test_send_summary_reports_missing_configuration(monkeypatch):
    monkeypatch.setattr(settings, "reporting_email_to", None)
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_from_email", None)

    result = asyncio.run(reporting_service.send_summary(SUMMARY))

    assert result["sent"] is False
    assert "REPORTING_EMAIL_TO" in result["reason"]
    assert "SMTP_HOST" in result["reason"]
    assert "SMTP_FROM_EMAIL" in result["reason"]


def test_send_summary_handles_smtp_failure(monkeypatch):
    configure_smtp(monkeypatch)

    class FailingSMTP:
        def __init__(self, *args, **kwargs):
            raise smtplib.SMTPConnectError(421, "unavailable")

    monkeypatch.setattr(reporting_service.smtplib, "SMTP", FailingSMTP)

    result = asyncio.run(reporting_service.send_summary(SUMMARY))

    assert result["sent"] is False
    assert result["reason"] == "SMTP delivery failed"
    assert result["error_type"] == "SMTPConnectError"


def test_reporting_lease_prevents_duplicate_run(db):
    assert reporting_service.claim_reporting_run(db, interval_seconds=3600) is True

    competing_worker = SessionLocal()
    try:
        assert reporting_service.claim_reporting_run(competing_worker, interval_seconds=3600) is False
    finally:
        competing_worker.close()

    schedule = db.get(ReportingSchedule, 1)
    assert schedule.last_started_at is not None
    assert schedule.next_run_at > schedule.last_started_at


def test_reporting_lease_can_be_reclaimed_after_window(db):
    assert reporting_service.claim_reporting_run(db, interval_seconds=3600) is True
    schedule = db.get(ReportingSchedule, 1)
    schedule.next_run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db.commit()

    assert reporting_service.claim_reporting_run(db, interval_seconds=3600) is True


def test_build_summary_excludes_completed_tasks(db):
    lead = Lead(name="Reporting Lead", email="reporting@example.com", lead_score=50)
    db.add(lead)
    db.flush()
    db.add_all(
        [
            Task(lead_id=lead.id, description="Still open", status="open"),
            Task(lead_id=lead.id, description="API completion", status="completed"),
            Task(lead_id=lead.id, description="Legacy completion", status="done"),
        ]
    )
    db.commit()

    assert reporting_service.build_summary(db)["open_tasks"] == 1
