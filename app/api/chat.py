"""
Chat API Router for Analytics Career Connect AI Assistant.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.knowledge.rag_engine import rag_engine
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    provider: Optional[str] = None # "local", "gemini", "openai", "groq"
    doc_filter: Optional[str] = None # Specific PDF filename or 'all'

class Citation(BaseModel):
    id: str
    source_name: str
    source_type: str
    title: str
    category: str
    page: Optional[int] = None
    url: Optional[str] = None
    snippet: str
    relevance_score: float

class ChatResponse(BaseModel):
    response: str
    provider: str
    citations: List[Citation]
    suggested_followups: List[str]

def generate_followups(query: str, response: str) -> List[str]:
    """Generates context-aware follow-up question suggestions."""
    q_low = query.lower()
    if "2027" in q_low or "2028" in q_low or "2029" in q_low or "student" in q_low:
        return [
            "Is the 2027-2029 internship 100% free?",
            "What is the stipend for top performing interns?",
            "How do I apply for the college internship?",
            "What skills will I learn during the internship?"
        ]
    elif "2026" in q_low or "placement" in q_low or "datayug" in q_low:
        return [
            "What are the 3 options under the DataYug Project?",
            "What placement support does ACC provide until placed?",
            "What tools (SQL, Power BI, Python) are covered in the placement program?",
            "Can non-technical/career switchers join the placement program?"
        ]
    elif "scam" in q_low or "fee" in q_low:
        return [
            "How do I verify official ACC communication?",
            "What programs are paid vs free?",
            "How to apply for official programs safely?"
        ]
    elif "founder" in q_low or "about" in q_low:
        return [
            "Tell me about the Founder's Office Internship",
            "What is ACC's mission and where are they based?",
            "What projects has ACC built?"
        ]
    else:
        return [
            "Compare Paid Placement Program vs College Internship",
            "What is the DataYug Project?",
            "Who founded Analytics Career Connect?",
            "What are the official application links?"
        ]

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    query = request.message.strip()

    # 1. Retrieve relevant knowledge chunks with optional document filter
    matched_chunks = rag_engine.search(query, top_k=5, source_filter=request.doc_filter)

    # 2. Build citations
    citations = []
    for c in matched_chunks:
        snippet = c.get("content", "")
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        citations.append(Citation(
            id=c.get("id", "c_0"),
            source_name=c.get("source_name", "ACC Knowledge Base"),
            source_type=c.get("source_type", "Document"),
            title=c.get("title", ""),
            category=c.get("category", "General"),
            page=c.get("page"),
            url=c.get("url"),
            snippet=snippet,
            relevance_score=c.get("relevance_score", 1.0)
        ))

    # 3. Generate response via LLM service (or local engine)
    result = await llm_service.generate_response(
        query=query,
        context_chunks=matched_chunks,
        conversation_history=request.history,
        provider=request.provider,
        company_profile=rag_engine.get_company_profile(),
        programs=rag_engine.get_all_programs(),
        doc_filter=request.doc_filter
    )

    # 4. Generate follow-ups
    followups = generate_followups(query, result["answer"])

    return ChatResponse(
        response=result["answer"],
        provider=result["provider"],
        citations=citations,
        suggested_followups=followups
    )

@router.get("/search")
async def search_endpoint(q: str, limit: int = 6):
    if not q or not q.strip():
        return {"results": []}
    results = rag_engine.search(q.strip(), top_k=limit)
    return {"results": results}
