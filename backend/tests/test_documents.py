from .conftest import MOCK_CHATBOT, MOCK_DOCUMENT, MOCK_SUPABASE_USER


def test_list_user_documents(documents_client, mock_documents_supabase):
	mock_documents_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
		MOCK_DOCUMENT
	]

	response = documents_client.get("/chatbots/documents")
	assert response.status_code == 200
	assert response.json()[0]["id"] == MOCK_DOCUMENT["id"]
	assert response.json()[0]["file_name"] == "sample.txt"


def test_list_chatbot_documents(documents_client, mock_documents_supabase):
	mock_documents_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
		MOCK_DOCUMENT
	]

	response = documents_client.get(f"/chatbots/{MOCK_CHATBOT['id']}/documents")
	assert response.status_code == 200
	assert response.json()[0]["chatbot_id"] == MOCK_CHATBOT["id"]


def test_upload_document(documents_client, mock_documents_supabase, mock_ingest_document):
	mock_documents_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = (
		MOCK_CHATBOT
	)
	mock_documents_supabase.storage.from_.return_value.get_public_url.return_value = MOCK_DOCUMENT["file_url"]
	mock_documents_supabase.table.return_value.insert.return_value.execute.return_value.data = [MOCK_DOCUMENT]

	response = documents_client.post(
		f"/chatbots/{MOCK_CHATBOT['id']}/documents",
		files={"file": ("sample.txt", b"hello world", "text/plain")},
	)

	assert response.status_code == 200
	assert response.json()["id"] == MOCK_DOCUMENT["id"]
	mock_documents_supabase.storage.from_.return_value.upload.assert_called_once()
	mock_ingest_document.assert_awaited_once()


def test_delete_document(documents_client, mock_documents_supabase, mock_documents_qdrant):
	mock_documents_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = (
		MOCK_DOCUMENT
	)

	response = documents_client.delete(f"/chatbots/{MOCK_CHATBOT['id']}/documents/{MOCK_DOCUMENT['id']}")

	assert response.status_code == 200
	assert response.json()["message"] == "document deleted successfully"
	mock_documents_supabase.storage.from_.return_value.remove.assert_called_once_with(
		[f"{MOCK_SUPABASE_USER['id']}/{MOCK_CHATBOT['id']}/sample.txt"]
	)
	mock_documents_qdrant.delete.assert_called_once()


def test_get_document_status(documents_client, mock_documents_supabase):
	mock_documents_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = {
		"id": MOCK_DOCUMENT["id"],
		"file_name": MOCK_DOCUMENT["file_name"],
		"status": "ready",
		"chunk_count": 8,
	}

	response = documents_client.get(f"/chatbots/{MOCK_CHATBOT['id']}/documents/{MOCK_DOCUMENT['id']}/status")

	assert response.status_code == 200
	assert response.json()["id"] == MOCK_DOCUMENT["id"]
	assert response.json()["status"] == "ready"
	assert response.json()["chunk_count"] == 8
