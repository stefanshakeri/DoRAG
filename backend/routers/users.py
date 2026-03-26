'''
User routes:
- GET:      /users/me       -> get current user profile
- PATCH:    /users/me       -> update user info
- GET:      /users/me/usage -> bot count, storage used, etc.
'''

from fastapi import APIRouter, Depends, HTTPException
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
        return UserProfile(**user.data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- PATCH:    /users/me       -> update user info
'''
@router.patch("/me")
async def update_profile(
    data: UserProfileUpdate,
    user_id: str = Depends(get_current_user)
) -> UserProfile:
    try:
        # only send provided fields
        updates = data.model_dump(exclude_none=True)
        user = supabase.table("profiles").update(updates).eq("id", user_id).execute()
        return UserProfile(**user.data[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- GET:      /users/me/usage -> bot count, storage used, etc.
'''
@router.get("/me/usage")
async def get_usage(user_id: str = Depends(get_current_user)) -> dict:
    try:
        # get chatbot count
        chatbots = supabase.table("chatbots").select("id", count="exact").eq("user_id", user_id).execute()
        # document count + storage used
        documents = supabase.table("documents").select("file_size_bytes").eq("user_id", user_id).execute()
        total_storage = sum(doc["file_size_bytes"] for doc in documents.data)

        return {
            "chatbot_count": chatbots.count,
            "document_count": len(documents.data),
            "storage_used_bytes": total_storage
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))