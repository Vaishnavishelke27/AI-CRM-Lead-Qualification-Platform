from services import ai_service


def test_scoring_uses_deterministic_fallback_without_provider(monkeypatch):
    monkeypatch.setattr(ai_service, "_call_ai", lambda *args, **kwargs: None)
    result = ai_service.score_lead_with_ai(
        {"company_size": "enterprise", "industry": "technology", "engagement_level": "high", "source": "referral"}
    )
    assert result["score"] == 100
    assert result["category"] == "Hot"


def test_scoring_normalizes_provider_output(monkeypatch):
    monkeypatch.setattr(ai_service, "_call_ai", lambda *args, **kwargs: {"score": 130, "reasoning": "provider"})
    result = ai_service.score_lead_with_ai({"email": "lead@example.com"})
    assert result["score"] == 100
    assert result["category"] == "Hot"


def test_email_generation_falls_back_when_provider_fails(monkeypatch):
    monkeypatch.setattr(ai_service, "_call_ai", lambda *args, **kwargs: {"error": "provider unavailable"})
    result = ai_service.generate_personalized_email(
        {"name": "Asha", "company": "Example Co"},
        purpose="follow_up",
        tone="professional",
    )
    assert result["subject"] == "Next steps for Example Co"
    assert "Hi Asha" in result["body"]
    assert result["personalization_notes"] == ["Generated with deterministic fallback."]
