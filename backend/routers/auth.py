'''
Authentication routes:
- POST:     /auth/logout    -> invalidate session
- DELETE:   /auth/account   -> account deletion
'''

from fastapi import APIRouter, Depends, HTTPException
from core.auth import get_current_user
from core.supabase import supabase_admin

router = APIRouter()

'''
- POST:     /auth/logout    -> invalidate session
'''
@router.post("/logout")
async def logout(user_id: str = Depends(get_current_user)) -> dict:
    try:
        supabase_admin.auth.admin.sign_out(user_id)
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
'''
- DELETE:   /auth/account   -> account deletion
'''
@router.delete("/account")
async def delete_account(user_id: str = Depends(get_current_user)) -> dict:
    try:
        # delete user from Supabase Auth (requires admin key)
        supabase_admin.auth.admin.delete_user(user_id)
        return {"message": "Account deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))