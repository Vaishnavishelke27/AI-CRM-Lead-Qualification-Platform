import hashlib
import json
import re
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any

from app.config import settings


class AIRateLimitError(RuntimeError):
    pass


@dataclass
class CachedValue:
    expires_at: float
    value: dict[str, Any]


class InMemoryTTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, CachedValue] = {}
        self._lock = Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            cached = self._items.get(key)
            if cached is None:
                return None
            if cached.expires_at <= now:
                self._items.pop(key, None)
                return None
            return cached.value

    def set(self, key: str, value: dict[str, Any]) -> None:
        with self._lock:
            self._items[key] = CachedValue(expires_at=time.time() + self.ttl_seconds, value=value)


class SlidingWindowRateLimiter:
    def __init__(self, max_calls: int, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: list[float] = []
        self._lock = Lock()

    def check(self) -> None:
        now = time.time()
        with self._lock:
            self._calls = [timestamp for timestamp in self._calls if now - timestamp < self.window_seconds]
            if len(self._calls) >= self.max_calls:
                raise AIRateLimitError("AI API rate limit exceeded")
            self._calls.append(now)


cache = InMemoryTTLCache(settings.ai_cache_ttl_seconds)
rate_limiter = SlidingWindowRateLimiter(settings.ai_rate_limit_per_minute)


def _cache_key(operation: str, payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, default=str)
    return f"{operation}:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def _extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _call_openai(prompt: str) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": "Return only valid JSON. Do not include markdown."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return _extract_json(response.choices[0].message.content or "{}")


def _call_claude(prompt: str) -> dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.claude_api_key)
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=1200,
        temperature=0.2,
        system="Return only valid JSON. Do not include markdown.",
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    return _extract_json(text or "{}")


def _call_ai(operation: str, payload: dict[str, Any], prompt: str) -> dict[str, Any] | None:
    key = _cache_key(operation, payload)
    cached = cache.get(key)
    if cached is not None:
        return {**cached, "cached": True}

    if not settings.openai_api_key and not settings.claude_api_key:
        return None

    rate_limiter.check()

    try:
        if settings.ai_provider == "claude" and settings.claude_api_key:
            value = _call_claude(prompt)
        elif settings.openai_api_key:
            value = _call_openai(prompt)
        elif settings.claude_api_key:
            value = _call_claude(prompt)
        else:
            return None
    except Exception as exc:
        return {"error": str(exc), "provider": settings.ai_provider}

    cache.set(key, value)
    return {**value, "cached": False}


def _category(score: int) -> str:
    if score >= 75:
        return "Hot"
    if score >= 45:
        return "Warm"
    return "Cold"


def deterministic_lead_score(lead_data: dict[str, Any]) -> dict[str, Any]:
    score = 20
    company_size = str(lead_data.get("company_size") or "").lower()
    industry = str(lead_data.get("industry") or "").lower()
    engagement = str(lead_data.get("engagement_level") or "").lower()
    source = str(lead_data.get("source") or "").lower()

    if company_size in {"enterprise", "1000+", "large"}:
        score += 25
    elif company_size in {"mid-market", "medium", "200-1000"}:
        score += 18
    elif company_size:
        score += 10

    if industry in {"saas", "software", "technology", "finance", "healthcare"}:
        score += 15
    elif industry:
        score += 8

    if engagement in {"high", "demo_requested", "pricing_page", "replied"}:
        score += 30
    elif engagement in {"medium", "webinar", "downloaded_asset"}:
        score += 18
    elif engagement:
        score += 8

    if source in {"referral", "demo", "webinar", "partner"}:
        score += 15
    elif source:
        score += 7

    score = max(0, min(score, 100))
    return {
        "score": score,
        "category": _category(score),
        "fallback": True,
        "reasoning": "Deterministic fallback score based on company size, industry, engagement level, and source.",
        "signals": {
            "company_size": company_size or None,
            "industry": industry or None,
            "engagement_level": engagement or None,
            "source": source or None,
        },
    }


def score_lead_with_ai(lead_data: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        "Score this CRM lead from 0-100 and categorize it as Hot, Warm, or Cold. "
        "Analyze company size, industry, engagement level, source, and any provided context. "
        "Return JSON with keys: score, category, reasoning, signals.\n\n"
        f"Lead data: {json.dumps(lead_data, default=str)}"
    )
    result = _call_ai("lead_score", lead_data, prompt)
    if result is None or "score" not in result:
        result = deterministic_lead_score(lead_data)

    score = int(result.get("score", 0))
    score = max(0, min(score, 100))
    result["score"] = score
    result["category"] = result.get("category") or _category(score)
    return result


def enrich_lead_with_ai(lead_data: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        "Enrich this CRM lead. Infer likely industry, company size, buyer persona, pain points, "
        "recommended next action, and confidence. Return JSON with keys: enrichment, insights, next_action, confidence.\n\n"
        f"Lead data: {json.dumps(lead_data, default=str)}"
    )
    result = _call_ai("lead_enrichment", lead_data, prompt)
    if result is not None and "error" not in result:
        return result

    return {
        "fallback": True,
        "enrichment": {
            "industry": lead_data.get("industry"),
            "company_size": lead_data.get("company_size"),
            "buyer_persona": "Unknown",
        },
        "insights": ["AI provider unavailable; stored fallback enrichment."],
        "next_action": "Review lead details and schedule manual follow-up.",
        "confidence": 0.35,
        **({"provider_error": result["error"]} if result and result.get("error") else {}),
    }


def generate_personalized_email(lead_data: dict[str, Any], purpose: str, tone: str) -> dict[str, Any]:
    payload = {"lead": lead_data, "purpose": purpose, "tone": tone}
    prompt = (
        "Generate a personalized CRM outreach email. Return JSON with keys: subject, body, personalization_notes. "
        f"Purpose: {purpose}. Tone: {tone}. Lead data: {json.dumps(lead_data, default=str)}"
    )
    result = _call_ai("generate_email", payload, prompt)
    if result is not None and result.get("subject") and result.get("body"):
        return result

    name = lead_data.get("name") or "there"
    company = lead_data.get("company") or "your team"
    return {
        "fallback": True,
        "subject": f"Next steps for {company}",
        "body": (
            f"Hi {name},\n\n"
            f"I wanted to follow up with a quick note tailored to {company}. "
            f"Based on your current interest, {purpose.replace('_', ' ')} seems like the right next step. "
            "Would you be open to a short conversation this week?\n\n"
            "Best,\nAI CRM Team"
        ),
        "personalization_notes": ["Generated with deterministic fallback."],
    }
