import os

import httpx
import pytest

RUN_LIVE_API_TESTS = os.getenv("RUN_LIVE_API_TESTS", "").lower() in {"1", "true", "yes"}
API_BASE_URL = os.getenv("DORAG_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_BEARER_TOKEN = os.getenv("DORAG_API_BEARER_TOKEN")
API_TIMEOUT_SECONDS = float(os.getenv("DORAG_API_TIMEOUT_SECONDS", "10"))
QDRANT_LIVE_URL = os.getenv("DORAG_QDRANT_URL", "").rstrip("/")
QDRANT_LIVE_API_KEY = os.getenv("DORAG_QDRANT_API_KEY")


pytestmark = pytest.mark.skipif(
    not RUN_LIVE_API_TESTS,
    reason="Live API tests are disabled. Set RUN_LIVE_API_TESTS=1 to enable.",
)


@pytest.fixture
def live_client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE_URL, timeout=API_TIMEOUT_SECONDS)


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
