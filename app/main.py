"""
FastAPI Server for Analytics Career Connect (ACC) AI Assistant.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.chat import router as chat_router
from app.api.programs import router as programs_router
from app.api.career_match import router as career_match_router
from app.api.documents import router as documents_router
from app.api.config import router as config_router

app = FastAPI(
    title="Analytics Career Connect (ACC) AI Assistant",
    description="Official AI Chatbot & Knowledge Assistant for ACC programs, internships, website, and career tracks.",
    version="2.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(chat_router)
app.include_router(programs_router)
app.include_router(career_match_router)
app.include_router(documents_router)
app.include_router(config_router)

# Mount Static Files
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Analytics Career Connect AI Assistant API is live. Access frontend at /"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ACC AI Chatbot"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
