'''
Document routes:
- GET:      /chatbots/{id}/documents                    -> list all docs for a chatbot
- POST:     /chatbots/{id}/documents                    -> upload file --> ingest pipeline
- DELETE:   /chatbots/{id}/documents/{doc_id}           -> delete doc from storage + Qdrant
- GET:      /chatbots/{id}/documents/{doc_id}/status    -> check ingestion status
'''