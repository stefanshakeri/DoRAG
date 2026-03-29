from fastapi import FastAPI

from routers import auth, chatbots, documents, chat, users

# from middleware.rate_limit import RateLimitMiddleware

app = FastAPI(title="DoRAG API")

# app.add_middleware(RateLimitMiddleware)

# include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chatbots.router, prefix="/chatbots", tags=["Chatbots"])
app.include_router(documents.router, prefix="/chatbots", tags=["Documents"])

'''
# uncomment when done implementing
app.include_router(chat.router, prefix="/chatbots", tags=["Chat"])
'''