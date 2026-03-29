from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import PointStruct

from core.qdrant import qdrant
from core.supabase import supabase
from core.redis import redis_client
from core.openai import embeddings_model
from config import settings

import tiktoken
import uuid
import pypdf
import docx
import io
import asyncio
import json

# parameters
CHUNK_SIZE = settings.chunk_size
CHUNK_OVERLAP = settings.chunk_overlap
INDIVIDUAL_TOKEN_LIMIT = settings.individual_token_limit
MAX_TOKENS = settings.max_tokens
MAX_ITEMS = settings.max_items
COOLDOWN_SECONDS = settings.cooldown_seconds
TTL_SECONDS = settings.ttl_seconds

enc = tiktoken.encoding_for_model("text-embedding-3-large")

async def ingest_document(
        chatbot_id: str,
        document_id: str,
        file_bytes: bytes,
        filename: str
):
    '''
    Ingest document into Qdrant collection:
    - update document status to "processing"
    - extract file text
    - chunk text
    - batch/embed chunks
    - store vectors
    - update document status to "ready"

    :param chatbot_id: chatbot ID (Qdrant collection name)
    :param document_id: document ID (Qdrant payload field)
    :param file_bytes: bytes of the file to ingest
    :param filename: name of the file
    '''
    skipped_chunks: list[str] = []

    try:
        # update document status to "processing"
        supabase.table("documents").update({"status": "processing"}).eq("id", document_id).execute()
        # extract file text
        text = extract_text(file_bytes, filename)
        # chunk text
        chunks = split_text(text)
        # batch/embed chunks
        points, skipped_chunks = await embed_and_collect(chunks, document_id, chatbot_id, filename)
        
        # store vectors
        qdrant.upsert(collection_name=chatbot_id, points=points)

        if skipped_chunks:
            await store_skipped_chunks(document_id, chatbot_id, filename, skipped_chunks)
            supabase.table("documents").update({
                "status": "partial",
                "chunk_count": len(points),
                "skipped_chunks": len(skipped_chunks)
            }).eq("id", document_id).execute()
            asyncio.create_task(retry_skipped_chunks(document_id, chatbot_id))
        else:
            # update document status to "ready"
            supabase.table("documents").update({"status": "ready", "chunk_count": len(points)}).eq("id", document_id).execute()

    except Exception as e:
        # if any error occurs, update document status to "failed"
        supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
        raise e
    

async def retry_skipped_chunks(document_id: str, chatbot_id: str):
    '''
    Wait for cooldown then retry embedding skipped chunks

    :param document_id: document ID (Qdrant payload field)
    :param chatbot_id: chatbot ID (Qdrant collection name)
    '''
    await asyncio.sleep(COOLDOWN_SECONDS)

    # retrieve skipped chunks from Redis
    redis_key = f"skipped_chunks:{document_id}"
    raw = await redis_client.get(redis_key)
    if not raw:
        return
    
    data = json.loads(raw)
    chunks = data["chunks"]
    filename = data["filename"]

    try:
        points, still_skipped = await embed_and_collect(chunks, document_id, chatbot_id, filename)
        if points:
            qdrant.upsert(collection_name=chatbot_id, points=points)
            await redis_client.delete(redis_key)

        if still_skipped:
            # store remaining skipped chunks, try again
            await store_skipped_chunks(document_id, chatbot_id, filename, still_skipped)
            asyncio.create_task(retry_skipped_chunks(document_id, chatbot_id))
            supabase.table("documents").update({
                "status": "partial",
                "skipped_chunks": len(still_skipped)
            }).eq("id", document_id).execute()
        else:
            # add to existing chunk count
            doc_response = supabase.table("documents").select("chunk_count").eq("id", document_id).execute()
            existing_count = doc_response.data[0]["chunk_count"] or 0   #type: ignore
            if type(existing_count) is not int:
                existing_count = 0
            supabase.table("documents").update({
                "status": "ready",
                "chunk_count": existing_count + len(points),
                "skipped_chunks": 0
            }).eq("id", document_id).execute()
    
    except Exception as e:
        supabase.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
        raise e
    

async def embed_and_collect(
        chunks: list[str],
        document_id: str,
        chatbot_id: str,
        filename: str
) -> tuple[list[PointStruct], list[str]]:
    '''
    Embed chunks and return (points, skipped_chunks)

    :param chunks: list of text chunks to embed
    :param document_id: document ID (Qdrant payload field)
    :param chatbot_id: chatbot ID (Qdrant collection name)
    :param filename: name of the file (used for logging)
    :returns: tuple of (list of PointStruct for successfully embedded chunks, list of skipped chunk texts)
    '''
    points: list[PointStruct] = []
    skipped: list[str] = []

    for batch, batch_skipped in make_batches(chunks):
        skipped.extend(batch_skipped)
        vectors = embeddings_model.embed_documents(batch)

        for chunk_text, vector in zip(batch, vectors):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk_text,
                        "document_id": document_id,
                        "chatbot_id": chatbot_id,
                        "filename": filename
                    }
                )
            )

    return points, skipped


async def store_skipped_chunks(
        document_id: str,
        chatbot_id: str,
        filename: str,
        chunks: list[str]
):
    '''
    Store skipped chunks in Redis w/ TTL so they don't persist forever

    :param document_id: document ID (Qdrant payload field)
    :param chatbot_id: chatbot ID (Qdrant collection name)
    :param filename: name of the file (used for logging)
    :param chunks: list of skipped chunk texts to store
    '''
    redis_key = f"skipped_chunks:{document_id}"
    await redis_client.setex(
        redis_key,
        TTL_SECONDS,
        json.dumps({
            "filename": filename,
            "chatbot_id": chatbot_id,
            "chunks": chunks
        })
    )


def extract_text(file_bytes: bytes, filename: str) -> str:
    '''
    Extract raw text from file bytes based on file type

    :param file_bytes: bytes of the file to extract
    :param filename: name of the file (used to determine file type)
    :returns: extracted text
    '''
    ext = filename.split(".")[-1].lower()

    if ext == "txt" or ext == "md":
        return file_bytes.decode("utf-8")
    
    elif ext == "pdf":
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    
    elif ext == "docx":
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(para.text for para in doc.paragraphs if para.text)
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def split_text(text: str) -> list[str]:
    '''
    Split text into chunks using LangChain

    :param text: raw text to split
    :returns: list of text chunks
    '''
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=lambda text: len(enc.encode(text)),
        add_start_index=False
    )
    return text_splitter.split_text(text)


def make_batches(chunks: list[str]):
    '''
    Yield (batch, skipped_chunks) that fit token limits. 
    
    :param chunks: list of text chunks to batch
    :yields: batches of text chunks
    '''
    batch: list[str] = []
    skipped_chunks: list[str] = []
    token_count = 0

    for chunk in chunks:
        tokens = len(enc.encode(chunk))

        if tokens > INDIVIDUAL_TOKEN_LIMIT:
            skipped_chunks.append(chunk)
            continue

        if token_count + tokens > MAX_TOKENS or len(batch) >= MAX_ITEMS:
            yield batch, skipped_chunks
            batch = []
            skipped_chunks = []
            token_count = 0

        batch.append(chunk)
        token_count += tokens

    if batch:
        yield batch, skipped_chunks
