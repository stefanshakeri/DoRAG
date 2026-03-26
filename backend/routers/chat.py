'''
Chat routes:
- POST:     /chatbots/{id}/chat                     -> send message, get RAG response
- GET:      /chatbots/{id}/conversations            -> list all conversations
- GET:      /chatbots/{id}/conversations/{conv_id}  -> get conversation history
- DELETE:   /chatbots/{id}/conversations/{conv_id}  -> delete a conversation
'''