def test_logout(client, mock_supabase_admin):
	response = client.post("/auth/logout")

	assert response.status_code == 200
	assert response.json()["message"] == "Logged out successfully"
	mock_supabase_admin.auth.admin.sign_out.assert_called_once_with("test-user-id-123")


def test_delete_account(client, mock_supabase_admin):
	response = client.delete("/auth/account")

	assert response.status_code == 200
	assert response.json()["message"] == "Account deleted successfully"
	mock_supabase_admin.auth.admin.delete_user.assert_called_once_with("test-user-id-123")
