from .conftest import MOCK_SUPABASE_USER

# test GET /users/me
def test_get_profile(client, mock_supabase):
    # mock supabase
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = MOCK_SUPABASE_USER
    
    response = client.get("/users/me")
    assert response.status_code == 200
    assert response.json()["id"] == "test-user-id-123"
    assert response.json()["email"] == "test@example.com"
    assert response.json()["username"] == "test_user"

# test PATCH /users/me
def test_update_profile(client, mock_supabase):
    # mock supabase
    updated_user = MOCK_SUPABASE_USER.copy()
    updated_user["username"] = "new_username"
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [updated_user]

    response = client.patch("/users/me", json={"username": "new_username"})
    assert response.status_code == 200
    assert response.json()["username"] == "new_username"

# test GET /users/me/usage
def test_get_usage(client, mock_supabase):
    # mock chatbot query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 2
    # mock documents query
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"file_size_bytes": 1000},
        {"file_size_bytes": 2000}
    ]

    response = client.get("/users/me/usage")
    assert response.status_code == 200
    assert response.json()["chatbot_count"] == 2
    assert response.json()["document_count"] == 2
    assert response.json()["storage_used_bytes"] == 3000