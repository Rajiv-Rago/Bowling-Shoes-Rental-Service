from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .endpoints import customers, rentals, chat
from .config import CORS_ORIGINS

app = FastAPI(
    title="Bowling Shoes Rental Service",
    description="API for managing bowling shoe rentals with an AI-powered chatbot assistant",
    version="2.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API routers
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(rentals.router, prefix="/rentals", tags=["rentals"])

# Chat/Agent router
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Bowling Shoes Rental Service",
        "version": "2.0.0",
        "features": [
            "REST API for customers and rentals",
            "AI-powered chatbot assistant via WebSocket",
            "Automatic discount calculations"
        ],
        "endpoints": {
            "api_docs": "/docs",
            "chat_websocket": "/chat/ws/{session_id}",
            "customers": "/customers/*",
            "rentals": "/rentals/*"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
