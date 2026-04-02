from pydantic import BaseModel, field_validator

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

    @field_validator("name")
    def name_must_be_valid(cls, v):
        if not v.strip():
            raise ValueError("Chatbot name must not be empty")
        if len(v) > 100:
            raise ValueError("Chatbot name exceeds maximum length of 100 characters")
        return v.strip()
    
    @field_validator("description")
    def description_length_check(cls, v):
        if v and len(v) > 1000:
            raise ValueError("Chatbot description exceeds maximum length of 1000 characters")
        return v.strip() if v else v

class ChatbotUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

    @field_validator("name")
    def name_must_be_valid(cls, v):
        if v is not None:
            if not v.strip():
                raise ValueError("Chatbot name must not be empty")
            if len(v) > 100:
                raise ValueError("Chatbot name exceeds maximum length of 100 characters")
            return v.strip()
        return v.strip() if v else v
    
    @field_validator("description")
    def description_length_check(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Chatbot description exceeds maximum length of 1000 characters")
            return v.strip()
        return v.strip() if v else v
    