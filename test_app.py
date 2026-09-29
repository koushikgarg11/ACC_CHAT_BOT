"""
Comprehensive Automated Test Suite for Analytics Career Connect AI Assistant.
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Set working directory to project root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from starlette.testclient import TestClient
from app.main import app
from app.knowledge.rag_engine import rag_engine

client = TestClient(app)

def test_health():
    print("Testing /health endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ /health passed!")

def test_rag_retrieval():
    print("\nTesting RAG Hybrid Search across key queries...")
    test_queries = [
        ("placement program 2026 batch", "Placement Program"),
        ("2027 2028 batch internship stipend free", "Internship"),
        ("scam alert fee charge", "Alert / Policy"),
        ("who is wasim patwari sadaf khan", "Company / Leadership"),
        ("datayug project option 1 option 2", "DataYug Project"),
        ("marketing intern remote", "Marketing")
    ]

    for q, domain in test_queries:
        results = rag_engine.search(q, top_k=3)
        assert len(results) > 0, f"No results for query: {q}"
        print(f"✅ RAG query '{q}' returned {len(results)} chunks. Top title: {results[0].get('title')} (score: {results[0].get('relevance_score')})")

def test_programs_endpoint():
    print("\nTesting /api/programs endpoint...")
    res = client.get("/api/programs")
    assert res.status_code == 200
    data = res.json()
    assert "programs" in data
    assert len(data["programs"]) >= 5
    print(f"✅ /api/programs returned {len(data['programs'])} structured programs.")

    # Filter test for 2027
    res_2027 = client.get("/api/programs?batch=2027")
    assert res_2027.status_code == 200
    data_2027 = res_2027.json()
    assert len(data_2027["programs"]) > 0
    print(f"✅ /api/programs?batch=2027 returned {len(data_2027['programs'])} student programs.")

def test_career_match_endpoint():
    print("\nTesting /api/career-match endpoint...")
    # Test for 2028 college student
    payload_student = {
        "graduation_year": 2028,
        "current_skills": ["SQL", "Excel"],
        "knowledge_level": "Beginner (0-30%)",
        "weekly_hours": 15,
        "target_role": "Data Analyst"
    }
    res = client.post("/api/career-match", json=payload_student)
    assert res.status_code == 200
    data = res.json()
    assert "2027" in data["recommended_program"]["batch"] or "College" in data["track_title"]
    print(f"✅ Career Match for 2028 batch matched track: {data['track_title']} (Fit Score: {data['skill_gap_analysis']['match_score_percentage']}%)")

    # Test for 2025 graduate
    payload_grad = {
        "graduation_year": 2025,
        "current_skills": ["SQL", "Power BI", "Python"],
        "knowledge_level": "Intermediate (30-70%)",
        "weekly_hours": 30,
        "target_role": "Data Analyst"
    }
    res_grad = client.post("/api/career-match", json=payload_grad)
    assert res_grad.status_code == 200
    data_grad = res_grad.json()
    assert "2026" in data_grad["recommended_program"]["batch"] or "Placement" in data_grad["track_title"] or "DataYug" in data_grad["track_title"]
    print(f"✅ Career Match for 2025 graduate matched track: {data_grad['track_title']}")

def test_documents_endpoint():
    print("\nTesting /api/documents endpoint...")
    res = client.get("/api/documents")
    assert res.status_code == 200
    data = res.json()
    assert len(data["pdf_documents"]) == 4
    assert len(data["website_pages"]) == 12
    print(f"✅ /api/documents returned 4 PDFs and 12 Website Pages (Total Chunks: {data['total_chunks_indexed']}).")

def test_single_pdf_endpoints():
    print("\nTesting Single PDF serving & page extraction endpoints...")
    test_pdf = "Marketing Intern (Remote _ Full-Time _ Part-Time).pdf"
    
    # 1. Test PDF File Serving
    res_pdf = client.get(f"/api/documents/pdf/{test_pdf}")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000
    print(f"✅ /api/documents/pdf/{test_pdf} returned binary PDF content ({len(res_pdf.content)} bytes).")

    # 2. Test Page-by-Page Extraction
    res_pages = client.get(f"/api/documents/pages/{test_pdf}")
    assert res_pages.status_code == 200
    pages_data = res_pages.json()
    assert pages_data["total_pages"] == 7
    assert len(pages_data["pages"]) == 7
    assert pages_data["pages"][0]["page_number"] == 1
    assert len(pages_data["pages"][0]["text"]) > 10
    print(f"✅ /api/documents/pages/{test_pdf} returned {pages_data['total_pages']} extracted pages with text & char counts.")

def test_chat_endpoint():
    print("\nTesting /api/chat endpoint with sample student and graduate queries...")
    chat_queries = [
        "Is the data analytics internship free or paid for 2027 batch students?",
        "What are the 3 options under DataYug Project?",
        "Who founded Analytics Career Connect?",
        "What tools and skills are taught in the placement curriculum?"
    ]

    for q in chat_queries:
        res = client.post("/api/chat", json={"message": q, "history": []})
        assert res.status_code == 200
        data = res.json()
        assert "response" in data and len(data["response"]) > 50
        assert "citations" in data
        assert "suggested_followups" in data
        print(f"✅ Query: '{q[:40]}...' -> Answer Length: {len(data['response'])} chars, Citations: {len(data['citations'])}, Provider: {data['provider']}")

def test_single_pdf_chat_filter():
    print("\nTesting /api/chat with single PDF doc_filter...")
    target_doc = "Marketing Intern (Remote _ Full-Time _ Part-Time).pdf"
    res = client.post("/api/chat", json={
        "message": "What is the duration and responsibilities for this marketing role?",
        "history": [],
        "doc_filter": target_doc
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["response"]) > 50
    assert len(data["citations"]) > 0
    # Citations should be from the target PDF
    for c in data["citations"]:
        assert target_doc.lower() in c["source_name"].lower() or "marketing" in c["source_name"].lower()
    print(f"✅ Single PDF chat filtered strictly to '{target_doc}'. Citations returned: {len(data['citations'])}.")

if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING AUTOMATED TESTS FOR ACC AI ASSISTANT")
    print("=" * 60)
    test_health()
    test_rag_retrieval()
    test_programs_endpoint()
    test_career_match_endpoint()
    test_documents_endpoint()
    test_single_pdf_endpoints()
    test_chat_endpoint()
    test_single_pdf_chat_filter()
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

