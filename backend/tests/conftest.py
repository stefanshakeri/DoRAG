import pytest
from fastapi.testclient import TestClient
from main import app
from core.auth import get_current_user

# mock user to avoid supabase authentication during tests
def mock_user():
    return "test-user-id-123"

# overrride auth dependency for tests
app.dependency_overrides[get_current_user] = mock_user

@pytest.fixture
def client():
    return TestClient(app)