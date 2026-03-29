import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# -----------------------------------------------
# Fixtures
# -----------------------------------------------

MOCK_CHATBOT = {
    "id": "test-chatbot-id",
    "user_id": "test-user-id-123",
    "name": "Test Bot",
    "system_prompt": "You are a helpful assistant.",
    "qdrant_collection": "test-chatbot-id",
    "created_at": "2024-01-01T00:00:00"
}

MOCK_CONVERSATION = {
    "id": "test-conv-id",
    "chatbot_id": "test-chatbot-id",
    "user_id": "test-user-id-123",
    "created_at": "2024-01-01T00:00:00"
}

MOCK_MESSAGES = [
    {"role": "user", "content": "Hello", "conversation_id": "test-conv-id"},
    {"role": "assistant", "content": "Hi there!", "conversation_id": "test-conv-id"}
]


# -----------------------------------------------
# POST /chatbots/{chatbot_id}/chat
# -----------------------------------------------

def test_chat_creates_new_conversation(client, mock_supabase):
    # mock chatbot lookup
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .single.return_value \
        .execute.return_value \
        .data = MOCK_CHATBOT

    # mock conversation insert
    mock_supabase.table.return_value \
        .insert.return_value \
        .execute.return_value \
        .data = [MOCK_CONVERSATION]

    # mock message insert
    mock_supabase.table.return_value \
        .insert.return_value \
        .execute.return_value \
        .data = MOCK_MESSAGES

    with patch("routers.chat.get_conversation_history", new_callable=AsyncMock) as mock_history, \
         patch("routers.chat.retrieve_context", new_callable=AsyncMock) as mock_context, \
         patch("routers.chat.generate_response", new_callable=AsyncMock) as mock_llm, \
         patch("routers.chat.update_conversation_cache", new_callable=AsyncMock):

        mock_history.return_value = []
        mock_context.return_value = "Relevant context from documents"
        mock_llm.return_value = "Hi there!"

        response = client.post(
            "/chatbots/test-chatbot-id/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 200
        assert response.json()["response"] == "Hi there!"
        assert "conversation_id" in response.json()


def test_chat_continues_existing_conversation(client, mock_supabase):
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .single.return_value \
        .execute.return_value \
        .data = MOCK_CHATBOT

    with patch("routers.chat.get_conversation_history", new_callable=AsyncMock) as mock_history, \
         patch("routers.chat.retrieve_context", new_callable=AsyncMock) as mock_context, \
         patch("routers.chat.generate_response", new_callable=AsyncMock) as mock_llm, \
         patch("routers.chat.update_conversation_cache", new_callable=AsyncMock):

        mock_history.return_value = MOCK_MESSAGES
        mock_context.return_value = "Relevant context"
        mock_llm.return_value = "How can I help?"

        response = client.post(
            "/chatbots/test-chatbot-id/chat",
            json={
                "message": "Follow up question",
                "conversation_id": "test-conv-id"
            }
        )

        assert response.status_code == 200
        assert response.json()["conversation_id"] == "test-conv-id"


def test_chat_chatbot_not_found(client, mock_supabase):
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .single.return_value \
        .execute.return_value \
        .data = None

    response = client.post(
        "/chatbots/nonexistent-id/chat",
        json={"message": "Hello"}
    )

    assert response.status_code == 404


def test_chat_empty_message(client, mock_supabase):
    response = client.post(
        "/chatbots/test-chatbot-id/chat",
        json={"message": ""}
    )
    # empty message should still hit the endpoint
    # you could add a validator to ChatRequest to reject empty strings
    assert response.status_code in [200, 400, 422]


# -----------------------------------------------
# GET /chatbots/{chatbot_id}/conversations
# -----------------------------------------------

def test_list_conversations(client, mock_supabase):
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .execute.return_value \
        .data = [MOCK_CONVERSATION]

    response = client.get("/chatbots/test-chatbot-id/conversations")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 1


def test_list_conversations_empty(client, mock_supabase):
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .execute.return_value \
        .data = []

    response = client.get("/chatbots/test-chatbot-id/conversations")

    assert response.status_code == 200
    assert response.json() == []


# -----------------------------------------------
# GET /chatbots/{chatbot_id}/conversations/{conv_id}
# -----------------------------------------------

def test_get_conversation_history(client, mock_supabase):
    # mock conversation ownership check
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .eq.return_value \
        .single.return_value \
        .execute.return_value \
        .data = MOCK_CONVERSATION

    # mock messages fetch
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .order.return_value \
        .execute.return_value \
        .data = MOCK_MESSAGES

    response = client.get("/chatbots/test-chatbot-id/conversations/test-conv-id")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_conversation_not_found(client, mock_supabase):
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .eq.return_value \
        .single.return_value \
        .execute.return_value \
        .data = None

    response = client.get("/chatbots/test-chatbot-id/conversations/nonexistent-id")

    assert response.status_code == 404


# -----------------------------------------------
# DELETE /chatbots/{chatbot_id}/conversations/{conv_id}
# -----------------------------------------------

def test_delete_conversation(client, mock_supabase):
    # mock ownership check
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .eq.return_value \
        .single.return_value \
        .execute.return_value \
        .data = MOCK_CONVERSATION

    with patch("routers.chat.redis_client") as mock_redis:
        mock_redis.delete = AsyncMock()

        response = client.delete("/chatbots/test-chatbot-id/conversations/test-conv-id")

        assert response.status_code == 200
        assert response.json()["message"] == "Conversation deleted successfully"
        mock_redis.delete.assert_called_once_with("context:test-conv-id")


def test_delete_conversation_not_found(client, mock_supabase):
    mock_supabase.table.return_value \
        .select.return_value \
        .eq.return_value \
        .eq.return_value \
        .eq.return_value \
        .single.return_value \
        .execute.return_value \
        .data = None

    response = client.delete("/chatbots/test-chatbot-id/conversations/nonexistent-id")

    assert response.status_code == 404