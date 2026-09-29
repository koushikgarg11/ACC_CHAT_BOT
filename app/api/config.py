"""
Config & LLM Provider API Router.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/config", tags=["Config"])

class UpdateKeysRequest(BaseModel):
    gemini_key: Optional[str] = None
    openai_key: Optional[str] = None
    groq_key: Optional[str] = None
    preferred_provider: Optional[str] = None

@router.get("/status")
async def get_config_status():
    """Returns current active providers and API key configuration status."""
    return llm_service.get_status()

@router.post("/keys")
async def update_keys(req: UpdateKeysRequest):
    """Updates API keys in memory."""
    llm_service.set_api_keys(
        gemini_key=req.gemini_key,
        openai_key=req.openai_key,
        groq_key=req.groq_key
    )
    if req.preferred_provider:
        llm_service.preferred_provider = req.preferred_provider

    return {
        "status": "success",
        "message": "Configuration updated successfully",
        "current_status": llm_service.get_status()
    }
