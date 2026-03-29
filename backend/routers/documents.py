'''
Document routes:
- GET:      /chatbots/documents                         -> list all docs for a user
- GET:      /chatbots/{id}/documents                    -> list all docs for a chatbot
- POST:     /chatbots/{id}/documents                    -> upload file --> ingest pipeline
- DELETE:   /chatbots/{id}/documents/{doc_id}           -> delete doc from storage + Qdrant
- GET:      /chatbots/{id}/documents/{doc_id}/status    -> check ingestion status
'''

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from qdrant_client.models import Filter, FieldCondition, MatchValue

from core.auth import get_current_user
from core.supabase import supabase
from core.qdrant import qdrant
from models.document import Document
from services.ingestion import ingest_document
from services.storage import upload_file, delete_file

router = APIRouter()

'''
- GET:      /chatbots/documents                         -> list all docs for a user
'''
@router.get("/documents")
async def list_user_documents(user_id: str = Depends(get_current_user)) -> list[Document]:
    try:
        documents = supabase.table("documents").select("*").eq("user_id", user_id).execute()
        return [Document(**cast(dict, doc)) for doc in documents.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
'''
- GET:      /chatbots/{id}/documents                    -> list all docs for a chatbot
'''
@router.get("/{chatbot_id}/documents")
async def list_documents(chatbot_id: str, user_id: str = Depends(get_current_user)) -> list[Document]:
    try:
        documents = supabase.table("documents").select("*").eq("chatbot_id", chatbot_id).eq("user_id", user_id).execute()
        return [Document(**cast(dict, doc)) for doc in documents.data]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- POST:     /chatbots/{id}/documents                    -> upload file --> ingest pipeline
'''
# TODO: finish upload_document
@router.post("/{chatbot_id}/documents")
# TODO: figure out document object type
async def upload_document(chatbot_id: str, file: UploadFile = File(...), user_id: str = Depends(get_current_user)) -> dict:
    try:
        # load chatbot
        chatbot = supabase.table("chatbots").select("*").eq("id", chatbot_id).eq("user_id", user_id).single().execute()
        if not chatbot.data:
            raise HTTPException(status_code=404, detail="Chatbot not found")
        
        # read file
        file_bytes = await file.read()
        filename = file.filename or "unknown"

        # upload to supabase storage
        file_url = upload_file(user_id, chatbot_id, filename, file_bytes, file.content_type or "application/octet-stream")

        doc = supabase.table("documents").insert({
            "chatbot_id": chatbot_id,
            "user_id": user_id,
            "file_name": filename,
            "file_url": file_url,
            "file_type": filename.split(".")[-1] if filename else "unknown",
            "file_size_bytes": len(file_bytes),
            "status": "pending"
        }).execute()
        # run ingestion pipeline
        doc_data = cast(list[dict], doc.data)
        doc_id = doc_data[0]["id"]
        await ingest_document(
            chatbot_id=chatbot_id,
            document_id=doc_id,
            file_bytes=file_bytes,
            filename=filename
        )

        return doc_data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- DELETE:   /chatbots/{id}/documents/{doc_id}           -> delete doc from storage + Qdrant
'''
# TODO: finish delete_document
@router.delete("/{chatbot_id}/documents/{doc_id}")
async def delete_document(chatbot_id: str, doc_id: str, user_id: str = Depends(get_current_user)) -> dict:
    try:        
        # delete document from supabase storage
        document_response = supabase.table("documents").select("*").eq("id", doc_id).eq("chatbot_id", chatbot_id).eq("user_id", user_id).single().execute()
        if not document_response.data:
            raise HTTPException(status_code=404, detail="Document not found")
        document = cast(dict, document_response.data)
        delete_file(user_id, chatbot_id, document['file_name'])
        
        # delete row from documents table
        supabase.table("documents").delete().eq("id", doc_id).execute()
        
        # delete assoc. vectors from Qdrant collection
        collection_name = str(chatbot_id)
        qdrant.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
        )

        return {"message": "document deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

'''
- GET:      /chatbots/{id}/documents/{doc_id}/status    -> check ingestion status
'''
@router.get("/{chatbot_id}/documents/{doc_id}/status")
async def get_document_status(doc_id: str, chatbot_id: str, user_id: str = Depends(get_current_user)) -> dict:
    try:
        document_response = supabase.table("documents").select("id, file_name, status, chunk_count").eq("id", doc_id).eq("chatbot_id", chatbot_id).eq("user_id", user_id).single().execute()
        if not document_response.data:
            raise HTTPException(status_code=404, detail="Document not found")
        return cast(dict, document_response.data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))