import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import recitation, flashcards

app = FastAPI(
    title="Smart Hadith Platform - AI Engine",
    description="APIs خاصة بمنصة الحديث الذكية - Clean Modular Architecture",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ربط المسارات (Routers)
app.include_router(recitation.router)
app.include_router(flashcards.router)

@app.get("/", tags=["Health Check"])
def home():
    return {
        "status": "online",
        "message": "Smart Hadith AI API is running (Phase 1 & Phase 2 Ready)",
        "endpoints": [
            "/api/v1/recitation/check",
            "/api/v1/flashcards/generate"
        ]
    }