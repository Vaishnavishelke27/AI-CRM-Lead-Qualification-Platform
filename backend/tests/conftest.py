import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-that-is-at-least-32-characters"
os.environ["REPORTING_INTERVAL_MINUTES"] = "999999"
os.environ["EMAIL_CLICK_ALLOWED_HOSTS"] = "crm.example"
os.environ["CRM_WEBHOOK_SECRET"] = "test-webhook-secret-that-is-at-least-32-characters"

import pytest

from app.database import Base, SessionLocal, engine


@pytest.fixture
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
