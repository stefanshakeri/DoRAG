from core.qdrant import qdrant
from langchain_openai import OpenAIEmbeddings

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")

async def retrieve_context(collection_name: str, query: str, top_k: int = 5) -> str:
    '''
    Retrieve relevant context from Qdrant collection based on user query

    :param collection_name: Qdrant collection name (chatbot ID)
    :param query: user query string
    :param top_k: number of relevant chunks to retrieve
    :returns: concatenated string of relevant context
    '''
    query_vector = embeddings_model.embed_query(query)
    results = qdrant.query_points(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k
    )

    if not results:
        return ""
    
    return "\n\n".join([
        str(r.payload["text"]) for r in results.points if r.payload is not None and "text" in r.payload
    ])