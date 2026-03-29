from .conftest import MOCK_SUPABASE_USER, MOCK_CHATBOT

class MockSingleResponse(dict):
	@property
	def data(self):
		return dict(self)


# test GET /chatbots
def test_list_chatbots(client, mock_chatbots_supabase):
	mock_chatbots_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
		MOCK_CHATBOT
	]

	response = client.get("/chatbots/")
	assert response.status_code == 200
	assert response.json()[0]["id"] == MOCK_CHATBOT["id"]
	assert response.json()[0]["name"] == "Support Bot"


# test POST /chatbots
def test_create_chatbot(client, mock_chatbots_supabase, mock_qdrant):
	mock_chatbots_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 1
	mock_chatbots_supabase.table.return_value.insert.return_value.execute.return_value.data = [MOCK_CHATBOT]

	response = client.post(
		"/chatbots/",
		json={"name": "Support Bot", "description": "Helps answer docs questions"},
	)

	assert response.status_code == 200
	assert response.json()["id"] == MOCK_CHATBOT["id"]
	mock_qdrant.create_collection.assert_called_once()


# test GET /chatbots/{id}
def test_get_chatbot(client, mock_chatbots_supabase):
	mock_chatbots_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = MockSingleResponse(
		MOCK_CHATBOT
	)

	response = client.get(f"/chatbots/{MOCK_CHATBOT['id']}")
	assert response.status_code == 200
	assert response.json()["id"] == MOCK_CHATBOT["id"]
	assert response.json()["user_id"] == MOCK_SUPABASE_USER["id"]


# test PATCH /chatbots/{id}
def test_update_chatbot(client, mock_chatbots_supabase):
	response = client.patch(
		f"/chatbots/{MOCK_CHATBOT['id']}",
		json={"name": "Renamed Bot"},
	)

	assert response.status_code == 200
	assert response.json()["message"] == "chatbot updated successfully"
	mock_chatbots_supabase.table.return_value.update.assert_called_once_with({"name": "Renamed Bot"})


# test DELETE /chatbots/{id}
def test_delete_chatbot(client, mock_chatbots_supabase, mock_qdrant):
	mock_chatbots_supabase.storage.from_.return_value.list.return_value = [
		{"name": "doc-1.pdf"},
		{"name": "doc-2.md"},
	]

	response = client.delete(f"/chatbots/{MOCK_CHATBOT['id']}")

	assert response.status_code == 200
	assert response.json()["message"] == "chatbot deleted successfully"
	mock_qdrant.delete_collection.assert_called_once_with(MOCK_CHATBOT["id"])
	mock_chatbots_supabase.storage.from_.return_value.remove.assert_called_once_with(
		[
			f"{MOCK_SUPABASE_USER['id']}/{MOCK_CHATBOT['id']}/doc-1.pdf",
			f"{MOCK_SUPABASE_USER['id']}/{MOCK_CHATBOT['id']}/doc-2.md",
		]
	)