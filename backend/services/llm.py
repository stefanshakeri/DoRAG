from fastapi import HTTPException

from core.openai import client
from core.redis import redis_client
from config import settings

SYSTEM_PROMPT = """
You are a chatbot assistant. Answer the question based only on the following context:
{context}

---

If the question cannot be answered based on the above context, say you don't know.
"""

async def generate_response(
    context: str,
    conversation_history: list[dict],
    user_message: str,
) -> str:
    '''
    Generate LLM response based on conversation history and RAG context

    :param context: retrieved context string from Qdrant
    :param conversation_history: list of dicts with "role" and "content" keys representing the conversation history
    :param user_message: the latest user message string
    '''
    # check OpenAI API budget before making the call
    await check_openai_budget()
    
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(context=context)
        },
        *conversation_history,
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages   # type: ignore
    )

    return response.choices[0].message.content or ""

async def check_openai_budget():
    '''
    Track daily OpenAI API call count globally. 
    Hard stop at limit to prevent runaway spend. 
    '''
    key = "openai:daily_calls"
    count = await redis_client.incr(key)

    # set TTL to end of day on first call
    if count == 1:
        await redis_client.expire(key, 86400)

    if count > settings.openai_daily_limit:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API daily limit exceeded. Please try again tomorrow."
        )