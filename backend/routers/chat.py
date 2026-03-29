'''
Chat routes:
- POST:     /chatbots/{id}/chat                     -> send message, get RAG response
- GET:      /chatbots/{id}/conversations            -> list all conversations
- GET:      /chatbots/{id}/conversations/{conv_id}  -> get conversation history
- DELETE:   /chatbots/{id}/conversations/{conv_id}  -> delete a conversation
'''

from typing import cast

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.supabase import supabase
from core.redis import redis_client
from services.retrieval import retrieve_context
from services.llm import generate_response
from models.chat import ChatRequest, ChatResponse

import json
import uuid

router = APIRouter()

'''
- POST:     /chatbots/{id}/chat                     -> send message, get RAG response
'''
@router.post("/{chatbot_id}/chat")
async def chat(chatbot_id: str, data: ChatRequest, user_id: str = Depends(get_current_user)) -> ChatResponse:
    try:
        # verify chatbot belongs to user
        chatbot = supabase.table("chatbots").select("*").eq("id", chatbot_id).eq("user_id", user_id).single().execute()
        if not chatbot.data:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        chatbot_data = cast(dict, chatbot.data)

        # get/create conversation
        conv_id = data.conversation_id
        if not conv_id:
            conv_id = str(uuid.uuid4())
            supabase.table("conversations").insert({
                "id": conv_id,
                "chatbot_id": chatbot_id,
                "user_id": user_id
            }).execute()
        
        # get conversation history from Redis (Supabase if needed)
        history = await get_conversation_history(conv_id)

        # retrieve relevant context from Qdrant
        context = await retrieve_context(chatbot_data["id"], data.message)

        # generate LLM response
        response_text = await generate_response(
            context=context,
            conversation_history=history,
            user_message=data.message
        )

        # save message to Supabase
        supabase.table("messages").insert([
            {
                "conversation_id": conv_id,
                "role": "user",
                "content": data.message
            },
            {
                "conversation_id": conv_id,
                "role": "assistant",
                "content": response_text
            }
        ]).execute()

        # update Redis cache
        await update_conversation_cache(conv_id, data.message, response_text)

        return ChatResponse(
            response=response_text,
            conversation_id=conv_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


'''
- GET:      /chatbots/{id}/conversations            -> list all conversations
'''
@router.get("/{chatbot_id}/conversations")
async def list_conversations(chatbot_id: str, user_id: str = Depends(get_current_user)) -> list[dict]:
    try:
        conversations = supabase.table("conversations").select("*").eq("chatbot_id", chatbot_id).eq("user_id", user_id).execute()
        return cast(list[dict], conversations.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

'''
- GET:      /chatbots/{id}/conversations/{conv_id}  -> get conversation history
'''
@router.get("/{chatbot_id}/conversations/{conv_id}")
async def get_conversation(
    chatbot_id: str,
    conv_id: str,
    user_id: str = Depends(get_current_user)
) -> list[dict]:
    try:
        # verify conversation belongs to user
        conversation = supabase.table("conversations").select("*").eq("id", conv_id).eq("chatbot_id", chatbot_id).eq("user_id", user_id).single().execute()
        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # get all conversation messages
        messages = supabase.table("messages").select("*").eq("conversation_id", conv_id).execute()
        return cast(list[dict], messages.data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

