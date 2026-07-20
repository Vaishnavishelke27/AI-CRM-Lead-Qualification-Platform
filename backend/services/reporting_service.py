import asyncio
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Lead, ReportingSchedule, Task


REPORTING_ADVISORY_LOCK_ID = 4_104_982_731


def claim_reporting_run(db: Session, interval_seconds: int) -> bool:
    now = datetime.now(timezone.utc)
    if db.bind.dialect.name == "postgresql":
        acquired = db.execute(
            text("SELECT pg_try_advisory_xact_lock(:lock_id)"),
            {"lock_id": REPORTING_ADVISORY_LOCK_ID},
        ).scalar_one()
        if not acquired:
            db.rollback()
            return False

    schedule = db.get(ReportingSchedule, 1, with_for_update=True)
    if schedule is None:
        schedule = ReportingSchedule(id=1, next_run_at=now)
        db.add(schedule)
        db.flush()

    if schedule.next_run_at > now:
        db.commit()
        return False

    schedule.last_started_at = now
    schedule.next_run_at = now + timedelta(seconds=max(1, interval_seconds))
    db.commit()
    return True


def build_summary(db: Session) -> dict:
    total = db.query(Lead).count()
    hot = db.query(Lead).filter(Lead.lead_score >= 75).count()
    converted = db.query(Lead).filter(Lead.status.in_(["converted", "won", "customer"])).count()
    open_tasks = db.query(Task).filter(Task.status.notin_(("completed", "done"))).count()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_leads": total,
        "hot_leads": hot,
        "conversion_rate": round((converted / total) * 100, 2) if total else 0,
        "open_tasks": open_tasks,
    }


def _summary_body(summary: dict) -> str:
    return "\n".join(
        [
            "AI CRM daily summary",
            "",
            f"Generated: {summary['generated_at']}",
            f"Total leads: {summary['total_leads']}",
            f"Hot leads: {summary['hot_leads']}",
            f"Conversion rate: {summary['conversion_rate']}%",
            f"Open tasks: {summary['open_tasks']}",
        ]
    )


def _send_summary_smtp(summary: dict) -> None:
    message = EmailMessage()
    message["Subject"] = "AI CRM daily summary"
    message["From"] = settings.smtp_from_email
    message["To"] = settings.reporting_email_to
    message.set_content(_summary_body(summary))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        smtp.ehlo()
        if settings.smtp_starttls:
            smtp.starttls()
            smtp.ehlo()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


async def send_summary(summary: dict) -> dict:
    missing = [
        name
        for name, value in {
            "REPORTING_EMAIL_TO": settings.reporting_email_to,
            "SMTP_HOST": settings.smtp_host,
            "SMTP_FROM_EMAIL": settings.smtp_from_email,
        }.items()
        if not value
    ]
    if missing:
        return {
            "sent": False,
            "reason": f"Missing email configuration: {', '.join(missing)}",
            "summary": summary,
        }

    try:
        await asyncio.to_thread(_send_summary_smtp, summary)
    except (OSError, smtplib.SMTPException) as exc:
        return {
            "sent": False,
            "reason": "SMTP delivery failed",
            "error_type": type(exc).__name__,
            "recipient": settings.reporting_email_to,
            "summary": summary,
        }

    return {"sent": True, "recipient": settings.reporting_email_to, "summary": summary}
