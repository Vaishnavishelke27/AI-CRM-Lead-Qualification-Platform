import os

import httpx
import pytest
from sqlalchemy import create_engine, text


@pytest.mark.skipif(not os.getenv("TEST_POSTGRES_URL"), reason="TEST_POSTGRES_URL is not configured")
def test_postgresql_connection():
    engine = create_engine(os.environ["TEST_POSTGRES_URL"], pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        engine.dispose()


@pytest.mark.parametrize("variable", ["DOCKER_BACKEND_URL", "RENDER_BACKEND_URL"])
def test_external_backend_health(variable):
    base_url = os.getenv(variable)
    if not base_url:
        pytest.skip(f"{variable} is not configured")
    response = httpx.get(f"{base_url.rstrip('/')}/health", timeout=15)
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok"}}
