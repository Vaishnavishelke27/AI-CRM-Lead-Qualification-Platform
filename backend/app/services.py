from app.models import Lead


def score_lead(lead_data: dict) -> tuple[int, str]:
    score = 30

    if lead_data.get("email"):
        score += 15
    if lead_data.get("company"):
        score += 20
    if lead_data.get("source") in {"referral", "demo", "webinar"}:
        score += 15

    score = max(0, min(score, 100))

    if score >= 75:
        category = "hot"
    elif score >= 45:
        category = "warm"
    else:
        category = "cold"

    return score, category


def build_task_description(lead: Lead) -> str:
    company = f" at {lead.company}" if lead.company else ""
    return f"Follow up with {lead.name}{company}"


def generate_email_content(lead: Lead, purpose: str, tone: str, subject: str | None) -> tuple[str, str]:
    email_subject = subject or f"Following up with {lead.company or lead.name}"
    company_reference = f" at {lead.company}" if lead.company else ""
    email_body = (
        f"Hi {lead.name},\n\n"
        f"I wanted to follow up on your interest{company_reference}. "
        f"Based on your current CRM status, I can help with next steps for {purpose}. "
        f"Let me know a convenient time to connect.\n\n"
        "Best,\n"
        "AI CRM Team"
    )

    if tone.lower() == "concise":
        email_body = (
            f"Hi {lead.name},\n\n"
            f"Following up on {purpose}. Are you available to discuss next steps this week?\n\n"
            "Best,\n"
            "AI CRM Team"
        )

    return email_subject, email_body
