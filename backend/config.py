from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    # Qdrant
    qdrant_url: str
    qdrant_api_key: str
    # OpenAI
    openai_api_key: str
    # Redis
    redis_url: str

    # Ingestion parameters
    chunk_size: int = 1500
    chunk_overlap: int = 200
    individual_token_limit: int = 8192
    max_tokens: int = 300000
    max_items: int = 2048
    cooldown_seconds: int = 60
    ttl_seconds: int = 3600

    class Config:
        env_file = ".env"

settings = Settings()   # type: ignore