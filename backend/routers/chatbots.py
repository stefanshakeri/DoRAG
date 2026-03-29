'''
Chatbot routes:
- GET:      /chatbots       -> list all chatbots for user
- POST:     /chatbots       -> create chatbot + Qdrant collection
- GET:      /chatbots/{id}  -> get single chatbot details
- PATCH:    /chatbots/{id}  -> update chatbot info
- DELETE:   /chatbots/{id}  -> delete chatbot + Qdrant collection
'''

from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client.models import VectorParams, Distance
from postgrest import CountMethod

from core.auth import get_current_user
from core.supabase import supabase
from core.qdrant import qdrant
from models.chatbot import Chatbot, ChatbotCreate, ChatbotUpdate
from services.storage import delete_chatbot_files

router = APIRouter()

'''
- GET:      /chatbots       -> list all chatbots for user
'''
@router.get("/")
async def list_chatbots(user_id: str = Depends(get_current_user)) -> list[Chatbot]:
    try:
        chatbots = supabase.table("chatbots").select("*").eq("user_id", user_id).execute()
        return [Chatbot(**cast(dict, c)) for c in chatbots.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- POST:     /chatbots       -> create chatbot + Qdrant collection
'''
@router.post("/")
async def create_chatbot(data: ChatbotCreate, user_id: str = Depends(get_current_user)) -> dict:
    try:
        # check chatbot limit
        existing = supabase.table("chatbots").select("id", count=CountMethod.exact).eq("user_id", user_id).execute()
        if existing.count is None:
            raise HTTPException(status_code=400, detail="Error checking chatbot count")
        if existing.count >= 3:
            raise HTTPException(status_code=403, detail="Chatbot limit reached (3)")
        
        # insert into supabase
        new_chatbot_response = supabase.table("chatbots").insert({
            "user_id": user_id,
            "name": data.name,
            "description": data.description
        }).execute()
        
        # create Qdrant collection
        new_chatbot = cast(list[dict], new_chatbot_response.data)[0]
        collection_name = new_chatbot["id"]
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)    # size 1536 for all OpenAI embedding models, COSINE distance empirically best for semantic search
        )

        return new_chatbot

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- GET:      /chatbots/{id}  -> get single chatbot details
'''
@router.get("/{chatbot_id}")
async def get_chatbot(chatbot_id: str, user_id: str = Depends(get_current_user)) -> Chatbot:
    try:
        chatbot = supabase.table("chatbots").select("*").eq("id", chatbot_id).eq("user_id", user_id).single().execute()
        if not chatbot.data:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        return Chatbot(**cast(dict, chatbot))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- PATCH:    /chatbots/{id}  -> update chatbot info
'''
@router.patch("/{chatbot_id}")
async def update_chatbot(data: ChatbotUpdate, chatbot_id: str, user_id: str = Depends(get_current_user)) -> dict:
    try:
        updates = data.model_dump(exclude_none=True)
        supabase.table("chatbots").update(updates).eq("id", chatbot_id).eq("user_id", user_id).execute()
        return {"message": "chatbot updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- DELETE:   /chatbots/{id}  -> delete chatbot + Qdrant collection
'''
@router.delete("/{chatbot_id}")
async def delete_chatbot(chatbot_id: str, user_id: str = Depends(get_current_user)) -> dict:
    try:
        qdrant.delete_collection(chatbot_id)
        supabase.table("chatbots").delete().eq("id", chatbot_id).eq("user_id", user_id).execute()
        # delete chatbot bucket, assoc. documents
        delete_chatbot_files(user_id, chatbot_id)
        return {"message": "chatbot deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

