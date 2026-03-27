'''
User routes:
- GET:      /users/me       -> get current user profile
- PATCH:    /users/me       -> update user info
- GET:      /users/me/usage -> bot count, storage used, etc.
'''
from typing import cast

from fastapi import APIRouter, Depends, HTTPException
from postgrest import CountMethod

from core.auth import get_current_user
from core.supabase import supabase
from models.user import UserProfile, UserProfileUpdate

router = APIRouter()

'''
- GET:      /users/me       -> get current user profile
'''
@router.get("/me")
async def get_profile(user_id: str = Depends(get_current_user)) -> UserProfile:
    try:
        user = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return UserProfile(**cast(dict, user.data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- PATCH:    /users/me       -> update user info
'''
@router.patch("/me")
async def update_profile(
    data: UserProfileUpdate,
    user_id: str = Depends(get_current_user)
) -> dict:
    try:
        # only send provided fields
        updates = data.model_dump(exclude_none=True)
        supabase.table("profiles").update(updates).eq("id", user_id).execute()
        return {"message": "profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- GET:      /users/me/usage -> bot count, storage used, etc.
'''
@router.get("/me/usage")
async def get_usage(user_id: str = Depends(get_current_user)) -> dict:
    try:
        # get chatbot count
        chatbots = supabase.table("chatbots").select("id", count=CountMethod.exact).eq("user_id", user_id).execute()
        # document count + storage used
        documents = supabase.table("documents").select("file_size_bytes").eq("user_id", user_id).execute()
        docs = cast(list[dict], documents.data)
        total_storage = sum(doc["file_size_bytes"] for doc in docs)

        return {
            "chatbot_count": chatbots.count,
            "document_count": len(documents.data),
            "storage_used_bytes": total_storage
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))