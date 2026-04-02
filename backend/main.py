from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, chatbots, documents, chat, users
from middleware.rate_limit import RateLimitMiddleware
from middleware.logging import LoggingMiddleware

app = FastAPI(title="DoRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(chatbots.router, prefix="/chatbots", tags=["Chatbots"])
app.include_router(documents.router, prefix="/chatbots", tags=["Documents"])
app.include_router(chat.router, prefix="/chatbots", tags=["Chat"])

