import os
from collections.abc import Iterator

import httpx
import pytest
import redis

RUN_LIVE_API_TESTS = os.getenv("RUN_LIVE_API_TESTS", "").lower() in {"1", "true", "yes"}
API_BASE_URL = os.getenv("DORAG_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_BEARER_TOKEN = os.getenv("DORAG_API_BEARER_TOKEN")
API_TIMEOUT_SECONDS = float(os.getenv("DORAG_API_TIMEOUT_SECONDS", "10"))
QDRANT_LIVE_URL = os.getenv("DORAG_QDRANT_URL", "").rstrip("/")
QDRANT_LIVE_API_KEY = os.getenv("DORAG_QDRANT_API_KEY")
SUPABASE_LIVE_URL = os.getenv("DORAG_SUPABASE_URL", "").rstrip("/")
SUPABASE_LIVE_API_KEY = os.getenv("DORAG_SUPABASE_API_KEY")
REDIS_LIVE_HOST = os.getenv("DORAG_REDIS_HOST", "")
REDIS_LIVE_PORT = int(os.getenv("DORAG_REDIS_PORT", "0") or 0)
REDIS_LIVE_USERNAME = os.getenv("DORAG_REDIS_USERNAME", "")
REDIS_LIVE_PASSWORD = os.getenv("DORAG_REDIS_PASSWORD", "")
REDIS_LIVE_USE_SSL = os.getenv("DORAG_REDIS_SSL", "").lower() in {"1", "true", "yes"}


pytestmark = pytest.mark.skipif(
    not RUN_LIVE_API_TESTS,
    reason="Live API tests are disabled. Set RUN_LIVE_API_TESTS=1 to enable.",
)


@pytest.fixture
def live_client() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=API_BASE_URL, timeout=API_TIMEOUT_SECONDS) as client:
        try:
            health_response = client.get("/health")
            health_response.raise_for_status()
        except httpx.HTTPError as exc:
            pytest.skip(f"Backend API not reachable at {API_BASE_URL}: {exc}")

        yield client


def test_live_health_endpoint(live_client: httpx.Client):
    response = live_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_live_docs_endpoint(live_client: httpx.Client):
    response = live_client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower()


def test_live_protected_route_requires_auth(live_client: httpx.Client):
    response = live_client.get("/users/me")

    assert response.status_code in {401, 403}


@pytest.mark.skipif(
    not API_BEARER_TOKEN,
    reason="Set DORAG_API_BEARER_TOKEN to validate authenticated live requests.",
)
def test_live_protected_route_with_token(live_client: httpx.Client):
    headers = {"Authorization": f"Bearer {API_BEARER_TOKEN}"}
    response = live_client.get("/users/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "id" in body


@pytest.mark.skipif(
    not QDRANT_LIVE_URL,
    reason="Set DORAG_QDRANT_URL to run live Qdrant API checks.",
)
def test_live_qdrant_collections_request():
    headers = {"Content-Type": "application/json"}
    if QDRANT_LIVE_API_KEY:
        headers["api-key"] = QDRANT_LIVE_API_KEY

    with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
        response = client.get(f"{QDRANT_LIVE_URL}/collections", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert "result" in body


@pytest.mark.skipif(
    not SUPABASE_LIVE_URL,
    reason="Set DORAG_SUPABASE_URL to run live Supabase API checks.",
)
def test_live_supabase_rest_request():
    headers = {"Accept": "application/openapi+json", "Content-Type": "application/json"}
    if SUPABASE_LIVE_API_KEY:
        headers["apikey"] = SUPABASE_LIVE_API_KEY
        headers["Authorization"] = f"Bearer {SUPABASE_LIVE_API_KEY}"

    with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
        response = client.get(f"{SUPABASE_LIVE_URL}/rest/v1/", headers=headers)

    # 200 means authorized openapi response; 401/403 still confirm request reached Supabase.
    assert response.status_code in {200, 401, 403}


@pytest.mark.skipif(
    not REDIS_LIVE_HOST or not REDIS_LIVE_PORT,
    reason="Set DORAG_REDIS_HOST and DORAG_REDIS_PORT to run live Redis connectivity checks.",
)
def test_live_redis_ping_request():
    redis_client = redis.Redis(
        host=REDIS_LIVE_HOST,
        port=REDIS_LIVE_PORT,
        username=REDIS_LIVE_USERNAME or None,
        password=REDIS_LIVE_PASSWORD or None,
        decode_responses=True,
        ssl=REDIS_LIVE_USE_SSL,
        socket_connect_timeout=API_TIMEOUT_SECONDS,
        socket_timeout=API_TIMEOUT_SECONDS,
    )

    try:
        assert redis_client.ping() is True
    finally:
        redis_client.close()
