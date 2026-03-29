import os

import pytest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Provide test-safe defaults so importing app settings never depends on real secrets/services.
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-supabase-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-supabase-service-key")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("QDRANT_API_KEY", "test-qdrant-api-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-api-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from main import app
from core.auth import get_current_user
from routers import documents as documents_router

MOCK_SUPABASE_USER = {
    "id": "test-user-id-123",
    "email": "test@example.com",
    "username": "test_user",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}

MOCK_CHATBOT = {
	"id": "test-chatbot-id-456",
	"user_id": MOCK_SUPABASE_USER["id"],
	"name": "Support Bot",
	"description": "Helps answer docs questions",
	"created_at": "2024-01-01T00:00:00Z",
	"updated_at": "2024-01-01T00:00:00Z",
}

MOCK_DOCUMENT = {
    "id": "test-doc-id-789",
    "chatbot_id": MOCK_CHATBOT["id"],
    "user_id": MOCK_SUPABASE_USER["id"],
    "file_name": "sample.txt",
    "file_url": "https://example.test/storage/sample.txt",
    "file_type": "txt",
    "file_size_bytes": 11,
    "chunk_count": 0,
    "status": "pending",
}

# mock user to avoid supabase authentication during tests
def mock_user():
    return "test-user-id-123"

# overrride auth dependency for tests
app.dependency_overrides[get_current_user] = mock_user

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def documents_client():
    test_app = FastAPI(title="DoRAG Documents Test API")
    test_app.dependency_overrides[get_current_user] = mock_user
    test_app.include_router(documents_router.router, prefix="/chatbots", tags=["Documents"])
    return TestClient(test_app)


@pytest.fixture
def mock_supabase():
    with patch("routers.users.supabase") as mock:
        yield mock


@pytest.fixture
def mock_chatbots_supabase():
    with patch("routers.chatbots.supabase") as mock:
        yield mock


@pytest.fixture
def mock_qdrant():
    with patch("routers.chatbots.qdrant") as mock:
        yield mock


@pytest.fixture
def mock_documents_supabase():
    with patch("routers.documents.supabase") as mock:
        yield mock


@pytest.fixture
def mock_documents_qdrant():
    with patch("routers.documents.qdrant") as mock:
        yield mock


@pytest.fixture
def mock_ingest_document():
    with patch("routers.documents.ingest_document", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_supabase_admin():
    with patch("routers.auth.supabase_admin") as mock:
        yield mock