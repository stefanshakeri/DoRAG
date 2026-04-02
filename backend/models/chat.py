from pydantic import BaseModel, field_validator

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None

    @field_validator("message")
    def message_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Message must not be empty")
        if len(v) > 5000:
            raise ValueError("Message exceeds maximum length of 5000 characters")
        return v.strip()

class ChatResponse(BaseModel):
    response: str
    conversation_id: str