import csv
from io import StringIO

from sqlalchemy.orm import Session

from app.models import Lead
from services.ai_service import score_lead_with_ai
from services.assignment_service import assign_lead


def import_leads_from_csv(csv_text: str, db: Session) -> dict:
    reader = csv.DictReader(StringIO(csv_text))
    created = 0
    skipped: list[dict] = []

    for row_number, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip()
        name = (row.get("name") or "").strip()
        if not email or not name:
            skipped.append({"row": row_number, "reason": "name and email are required"})
            continue
        if db.query(Lead).filter(Lead.email == email).first():
            skipped.append({"row": row_number, "reason": "duplicate email", "email": email})
            continue

        payload = {
            "name": name,
            "email": email,
            "company": (row.get("company") or "").strip() or None,
            "source": (row.get("source") or "csv_import").strip(),
            "status": (row.get("status") or "new").strip(),
            "company_size": row.get("company_size"),
            "industry": row.get("industry"),
            "engagement_level": row.get("engagement_level"),
        }
        ai_score = score_lead_with_ai(payload)
        lead = Lead(
            name=payload["name"],
            email=payload["email"],
            company=payload["company"],
            source=payload["source"],
            status=payload["status"],
            lead_score=ai_score["score"],
            category=ai_score["category"],
            ai_metadata={"score": ai_score, "import": {"row": row_number}},
        )
        db.add(lead)
        db.flush()
        assign_lead(lead)
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped}
