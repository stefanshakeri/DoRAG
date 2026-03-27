from pydantic import BaseModel

# Supabase profiles table schema
class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    created_at: str
    updated_at: str

class UserProfileUpdate(BaseModel):
    username: str | None = None