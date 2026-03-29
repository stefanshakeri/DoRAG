from core.openai import client

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