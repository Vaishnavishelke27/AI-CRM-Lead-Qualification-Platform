from app.models import Lead


SALES_ROUTES = {
    "Hot": ["enterprise-ae@crm.local", "senior-ae@crm.local"],
    "Warm": ["growth-ae@crm.local", "midmarket-ae@crm.local"],
    "Cold": ["sdr@crm.local", "nurture@crm.local"],
}


def assign_lead(lead: Lead) -> str:
    category = lead.category or ("Hot" if lead.lead_score >= 75 else "Warm" if lead.lead_score >= 45 else "Cold")
    routes = SALES_ROUTES.get(category, SALES_ROUTES["Cold"])
    assignee = routes[lead.id % len(routes)] if lead.id else routes[0]
    lead.assigned_to = assignee
    lead.ai_metadata = {
        **(lead.ai_metadata or {}),
        "assignment": {"assigned_to": assignee, "category": category, "score": lead.lead_score},
    }
    return assignee
