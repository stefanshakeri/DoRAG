from pydantic import BaseModel

# Supabase chatbots table schema
class Chatbot(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None = None
    created_at: str
    updated_at: str

class ChatbotCreate(BaseModel):
    name: str
    description: str | None = None

class ChatbotUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    