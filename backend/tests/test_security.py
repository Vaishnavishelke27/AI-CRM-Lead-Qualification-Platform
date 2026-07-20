import asyncio
import os
from datetime import timezone

import pytest
from fastapi import HTTPException, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.pool import StaticPool

from app.database import engine
from app.config import load_environment
from app.main import app, lead_updates_websocket, lifespan, register_user, track_email_click
from app.models import Email, Lead
from app.schemas import UserCreate
from services.auth_service import authenticate_webhook_or_user, create_access_token, get_current_user
from services.websocket_manager import manager


class FakeWebSocket:
    def __init__(self, auth_message):
        self.auth_message = auth_message
        self.accepted = False
        self.closed = None
        self.sent = []

    async def accept(self):
        self.accepted = True

    async def receive_json(self):
        return self.auth_message

    async def send_json(self, message):
        self.sent.append(message)

    async def receive_text(self):
        raise WebSocketDisconnect()

    async def close(self, code, reason):
        self.closed = {"code": code, "reason": reason}


def test_public_registration_rejects_role_injection():
    with pytest.raises(ValidationError):
        UserCreate.model_validate(
            {
                "email": "attacker@example.com",
                "full_name": "Attacker",
                "password": "password123",
                "role": "admin",
            }
        )


def test_public_registration_assigns_sales_role(db):
    user = register_user(
        UserCreate(email="sales@example.com", full_name="Sales User", password="password123"),
        db,
    )
    assert user.role == "sales"


@pytest.mark.parametrize(
    ("method", "path", "authentication_dependency"),
    [
        ("POST", "/leads", get_current_user),
        ("GET", "/leads", get_current_user),
        ("GET", "/leads/{lead_id}", get_current_user),
        ("PUT", "/leads/{lead_id}", get_current_user),
        ("DELETE", "/leads/{lead_id}", get_current_user),
        ("GET", "/tasks", get_current_user),
        ("POST", "/tasks", get_current_user),
        ("GET", "/emails", get_current_user),
        ("POST", "/emails/generate", get_current_user),
        ("POST", "/webhooks/lead-enrichment", authenticate_webhook_or_user),
        ("POST", "/webhooks/lead-score", authenticate_webhook_or_user),
    ],
)
def test_crm_routes_require_authentication(method, path, authentication_dependency):
    route = next(route for route in app.routes if getattr(route, "path", None) == path and method in route.methods)
    dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
    assert authentication_dependency in dependency_calls


def test_click_tracking_rejects_invalid_token(db):
    with pytest.raises(HTTPException) as error:
        track_email_click("not-real", "https://crm.example/path", db)
    assert error.value.status_code == 404


def test_click_tracking_rejects_unapproved_host(db):
    lead = Lead(name="Lead", email="lead@example.com", lead_score=50, ai_metadata={})
    db.add(lead)
    db.flush()
    db.add(Email(lead_id=lead.id, subject="Subject", body="Body", tracking_token="valid-token"))
    db.commit()

    with pytest.raises(HTTPException) as error:
        track_email_click("valid-token", "https://evil.example/phish", db)
    assert error.value.status_code == 400


def test_in_memory_sqlite_uses_static_pool():
    assert isinstance(engine.pool, StaticPool)


def test_sqlite_round_trip_preserves_utc_timezone(db):
    lead = Lead(name="Timezone Lead", email="timezone@example.com", lead_score=50, ai_metadata={})
    db.add(lead)
    db.commit()
    db.refresh(lead)
    assert lead.created_at.tzinfo is timezone.utc


def test_lifespan_starts_and_stops_reporting_task():
    async def exercise_lifespan():
        async with lifespan(app):
            reporting_task = app.state.reporting_task
            assert not reporting_task.done()
        assert reporting_task.cancelled()

    asyncio.run(exercise_lifespan())


def test_environment_file_loads_without_overriding_shell(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("ENV_FILE_ONLY=loaded\nSHELL_VALUE=from-file\n", encoding="utf-8")
    monkeypatch.delenv("ENV_FILE_ONLY", raising=False)
    monkeypatch.setenv("SHELL_VALUE", "from-shell")

    load_environment(env_file)

    assert os.environ["ENV_FILE_ONLY"] == "loaded"
    assert os.environ["SHELL_VALUE"] == "from-shell"


def test_websocket_authenticates_with_first_message(db):
    user = register_user(
        UserCreate(email="socket@example.com", full_name="Socket User", password="password123"),
        db,
    )
    token = create_access_token(user.email, user.role)
    websocket = FakeWebSocket({"type": "authenticate", "token": token})

    asyncio.run(lead_updates_websocket(websocket))

    assert websocket.accepted
    assert websocket.closed is None
    assert websocket.sent == [{"type": "authenticated"}]
    assert websocket not in manager.active_connections


def test_websocket_rejects_invalid_first_message():
    websocket = FakeWebSocket({"type": "authenticate", "token": "invalid"})

    asyncio.run(lead_updates_websocket(websocket))

    assert websocket.accepted
    assert websocket.closed == {"code": 1008, "reason": "Authentication required"}
    assert websocket not in manager.active_connections
