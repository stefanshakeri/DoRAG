'''
Extract + validate user ID from JWT
'''

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from core.supabase import supabase

security = HTTPBearer()

async def get_current_user(token = Depends(security)) -> str:
    try:
        # verify the JWT token with Supabase
        user = supabase.auth.get_user(token.credentials)
        return user.user.id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")