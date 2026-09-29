"""
Programs & Company API Router.
"""

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from app.knowledge.rag_engine import rag_engine

router = APIRouter(prefix="/api", tags=["Programs & Company"])

@router.get("/programs")
async def get_programs(batch: Optional[int] = None, q: Optional[str] = None):
    """Returns list of ACC programs with optional batch year or search filter."""
    if batch:
        progs = rag_engine.get_program_by_batch(batch)
    else:
        progs = rag_engine.get_all_programs()

    if q:
        q_low = q.lower()
        progs = [
            p for p in progs
            if q_low in p["title"].lower()
            or q_low in p["description"].lower()
            or any(q_low in s.lower() for s in p.get("key_skills", []))
        ]

    return {"programs": progs, "count": len(progs)}

@router.get("/company")
async def get_company_info():
    """Returns company profile, mission, leadership, scam alert, and FAQs."""
    return rag_engine.get_company_profile()
