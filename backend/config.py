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

    class Config:
        env_file = ".env"

settings = Settings()   # type: ignore