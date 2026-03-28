from pydantic import BaseModel

class Document(BaseModel):
    id: str
    chatbot_id: str
    user_id: str
    file_name: str
    file_url: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    status: str