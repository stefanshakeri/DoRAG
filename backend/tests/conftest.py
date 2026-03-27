import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from core.auth import get_current_user

MOCK_SUPABASE_USER = {
    "id": "test-user-id-123",
    "email": "test@example.com",
    "username": "test_user",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
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
def mock_supabase():
    with patch("routers.users.supabase") as mock:
        yield mock