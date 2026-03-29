from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from config import settings

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
client = AsyncOpenAI(api_key=settings.openai_api_key)