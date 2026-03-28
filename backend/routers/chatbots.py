'''
Chatbot routes:
- GET:      /chatbots       -> list all chatbots for user
- POST:     /chatbots       -> create chatbot + Qdrant collection
- GET:      /chatbots/{id}  -> get single chatbot details
- PATCH:    /chatbots/{id}  -> update chatbot info
- DELETE:   /chatbots/{id}  -> delete chatbot + Qdrant collection
'''

from typing import cast
import json

from fastapi import APIRouter, Depends, HTTPException

from core.auth import get_current_user
from core.supabase import supabase
from core.qdrant import qdrant
from models.chatbot import Chatbot, ChatbotCreate, ChatbotUpdate

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
        # TODO: remove qdrant_collection field from Supabase "chatbots" table
        chatbot = {
            "user_id": user_id,
            "name": data.name,
            "description": data.description
        }
        new_chatbot_response = supabase.table("chatbots").insert(json.dumps(chatbot)).execute()
        # create new Qdrant collection
        new_chatbot = new_chatbot_response.model_dump()
        qdrant.create_collection(
            collection_name = new_chatbot["id"]
        )        
        return {"message": "chatbot created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- GET:      /chatbots/{id}  -> get single chatbot details
'''
@router.get("/{id}")
async def get_chatbot(chatbot_id: str) -> Chatbot:
    try:
        chatbot = supabase.table("chatbots").select("*").eq("id", chatbot_id).single().execute()
        return Chatbot(**cast(dict, chatbot))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- PATCH:    /chatbots/{id}  -> update chatbot info
'''
@router.patch("/{id}")
async def update_chatbot(data: ChatbotUpdate, chatbot_id: str) -> dict:
    try:
        updates = data.model_dump(exclude_none=True)
        supabase.table("chatbots").update(updates).eq("id", chatbot_id).execute()
        return {"message": "chatbot updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- DELETE:   /chatbots/{id}  -> delete chatbot + Qdrant collection
'''
@router.delete("/{id}")
async def delete_chatbot(chatbot_id: str, user_id: str = Depends(get_current_user)) -> dict:
    try:
        qdrant.delete_collection(chatbot_id)
        supabase.table("chatbots").delete().eq("id", chatbot_id).execute()
        # delete chatbot bucket, assoc. documents
        files = supabase.storage.from_("documents").list(f"{user_id}/{chatbot_id}")
        paths = [f"{user_id}/{chatbot_id}/{f['name']}" for f in files]
        supabase.storage.from_("documents").remove(paths)
        return {"message": "chatbot deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

