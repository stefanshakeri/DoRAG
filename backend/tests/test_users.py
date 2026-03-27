# test GET /users/me
def test_get_profile(client):
    response = client.get("/users/me")
    assert response.status_code == 200
    assert "email" in response.json()
    assert "username" in response.json()

# test PATCH /users/me
def test_update_profile(client):
    response = client.patch("/users/me", json={"username": "test_user"})
    assert response.status_code == 200
    assert response.json()["username"] == "test_user"

# test GET /users/me/usage
def test_get_usage(client):
    response = client.get("/users/me/usage")
    assert response.status_code == 200
    assert "chatbot_count" in response.json()
    assert "document_count" in response.json()
    assert "storage_used_bytes" in response.json()