from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Lead, Task


def build_summary(db: Session) -> dict:
    total = db.query(Lead).count()
    hot = db.query(Lead).filter(Lead.lead_score >= 75).count()
    converted = db.query(Lead).filter(Lead.status.in_(["converted", "won", "customer"])).count()
    open_tasks = db.query(Task).filter(Task.status != "done").count()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_leads": total,
        "hot_leads": hot,
        "conversion_rate": round((converted / total) * 100, 2) if total else 0,
        "open_tasks": open_tasks,
    }


async def send_summary(summary: dict) -> dict:
    if not settings.reporting_email_to:
        return {"sent": False, "reason": "REPORTING_EMAIL_TO is not configured", "summary": summary}

    # Placeholder for transactional email provider integration.
    async with httpx.AsyncClient(timeout=10) as client:
        return {
            "sent": False,
            "reason": "Email provider endpoint not configured",
            "recipient": settings.reporting_email_to,
            "summary": summary,
            "client": client.__class__.__name__,
        }
