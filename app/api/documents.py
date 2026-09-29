"""
Documents & Upload Explorer API Router.
"""

import os
import io
import pypdf
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from app.knowledge.rag_engine import rag_engine

router = APIRouter(prefix="/api", tags=["Documents"])

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@router.get("/documents")
async def get_documents():
    """Lists all indexed PDF documents and website pages with metadata."""
    pdf_details = [
        {
            "filename": "JD Paid Placement Program With Internship  (1).pdf",
            "title": "Paid Placement Program With Internship (Data Analytics)",
            "pages": 10,
            "category": "Placement Track",
            "target_batch": "2026 & Below",
            "description": "Comprehensive job description for the paid placement acceleration track. Highlights 100% placement support, 1:1 mentorship, live projects, and scam prevention notice."
        },
        {
            "filename": "Marketing Intern (Remote _ Full-Time _ Part-Time).pdf",
            "title": "Marketing Internship Program",
            "pages": 7,
            "category": "Marketing & Growth",
            "target_batch": "2010 – 2030",
            "description": "Details the remote marketing internship role, founder leadership under Mr. Wasim Patwari and Mrs. Sadaf Khan, performance-based incentives, and startup growth responsibilities."
        },
        {
            "filename": "PDF Data &amp; Business Analyst Intern _ Remote] _ 2027_2028_2029 Batch .pdf",
            "title": "Data & Business Analyst Internship (College Students)",
            "pages": 13,
            "category": "Student Internship",
            "target_batch": "2027, 2028, 2029 Batches",
            "description": "100% free internship for college students. Covers Excel, SQL, Power BI, Python, performance stipends (₹5K-₹10K), official LOR, and scam warnings."
        },
        {
            "filename": "Under DataYug Project Data Analyst JD ( 2026 and Below ) JD (5) (1) (1).pdf",
            "title": "DataYug Project - Data Analyst Opportunities",
            "pages": 10,
            "category": "Placement & Project Tracks",
            "target_batch": "2026 & Earlier",
            "description": "Details the 3 specialized tracks: Option 1 (General Internship for 80%+ knowledge), Option 2 (Guided Track), Option 3 (Full Placement Program)."
        }
    ]

    website_pages = [
        {"name": "Home Page", "url": "https://analyticscareerconnect.com/", "topics": "Company mission, vision, overview, stats"},
        {"name": "Program", "url": "https://analyticscareerconnect.com/program/", "topics": "Core analytics curriculum, tools, projects"},
        {"name": "Placement Program", "url": "https://analyticscareerconnect.com/placement-program/", "topics": "Guaranteed assistance, 1:1 mentorship, corporate projects"},
        {"name": "Mentorship Program", "url": "https://analyticscareerconnect.com/mentorship-program/", "topics": "1-on-1 industry mentor guidance, portfolio audits"},
        {"name": "Job Assistance Program", "url": "https://analyticscareerconnect.com/job-assistance-program/", "topics": "ATS resume rebuilding, interview preparation, partner referrals"},
        {"name": "Service", "url": "https://analyticscareerconnect.com/service/", "topics": "IT, recruitment, training, corporate solutions"},
        {"name": "About Us", "url": "https://analyticscareerconnect.com/about-us/", "topics": "Pune HQ, founders story, vision, core values"},
        {"name": "Career Page", "url": "https://analyticscareerconnect.com/careerpage/", "topics": "Open roles, internship openings, life at ACC"},
        {"name": "Intern", "url": "https://analyticscareerconnect.com/intern/", "topics": "2027-2029 batch free internships, live tasks"},
        {"name": "Summer Internship", "url": "https://analyticscareerconnect.com/summer-internship/", "topics": "Fast-track summer programs for college students"},
        {"name": "Founder's Office", "url": "https://analyticscareerconnect.com/founders-office/", "topics": "Direct executive internships with Founders"},
        {"name": "Contact Us", "url": "https://analyticscareerconnect.com/contact-us/", "topics": "Office address, email, social handles, support"}
    ]

    return {
        "pdf_documents": pdf_details,
        "website_pages": website_pages,
        "total_chunks_indexed": len(rag_engine.chunks)
    }

from fastapi.responses import FileResponse
import urllib.parse

@router.get("/documents/pdf/{filename:path}")
async def serve_pdf_file(filename: str):
    """Serves the actual PDF file for browser viewing."""
    decoded_name = urllib.parse.unquote(filename)
    filepath = os.path.join(WORKSPACE_DIR, decoded_name)
    
    # Try alternate naming if &amp; vs & mismatch
    if not os.path.exists(filepath):
        alt_name = decoded_name.replace("&", "&amp;")
        alt_path = os.path.join(WORKSPACE_DIR, alt_name)
        if os.path.exists(alt_path):
            filepath = alt_path

    if not os.path.exists(filepath) or not filepath.endswith(".pdf"):
        raise HTTPException(status_code=404, detail=f"PDF document '{filename}' not found.")

    return FileResponse(
        filepath,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{os.path.basename(filepath)}"'}
    )

@router.get("/documents/pages/{filename:path}")
async def get_document_pages(filename: str):
    """Extracts and returns structured page-by-page content for a single PDF document."""
    decoded_name = urllib.parse.unquote(filename)
    filepath = os.path.join(WORKSPACE_DIR, decoded_name)

    if not os.path.exists(filepath):
        alt_name = decoded_name.replace("&", "&amp;")
        alt_path = os.path.join(WORKSPACE_DIR, alt_name)
        if os.path.exists(alt_path):
            filepath = alt_path

    if not os.path.exists(filepath) or not filepath.endswith(".pdf"):
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found.")

    try:
        reader = pypdf.PdfReader(filepath)
        pages_data = []
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages_data.append({
                "page_number": page_idx + 1,
                "text": text.strip(),
                "char_count": len(text)
            })
        
        file_size_kb = round(os.path.getsize(filepath) / 1024, 1)

        return {
            "filename": os.path.basename(filepath),
            "total_pages": len(reader.pages),
            "file_size_kb": file_size_kb,
            "pages": pages_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read PDF pages: {e}")

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a candidate resume or custom document and parses it for immediate Q&A."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file.")

    content_bytes = await file.read()
    extracted_text = ""

    if file.filename.lower().endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            for page in reader.pages:
                text = page.extract_text() or ""
                extracted_text += text + "\n"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")
    elif file.filename.lower().endswith((".txt", ".md")):
        extracted_text = content_bytes.decode("utf-8", errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Supported formats: .pdf, .txt, .md")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the uploaded file.")

    # Index into session knowledge chunks
    chunk_id = f"custom_upload_{file.filename[:8]}"
    new_chunk = {
        "id": chunk_id,
        "source_type": "User Uploaded Document",
        "source_name": file.filename,
        "title": f"Custom Upload: {file.filename}",
        "category": "Candidate Profile / Custom Doc",
        "target_batch": "Custom",
        "page": 1,
        "content": extracted_text[:2500], # Keep relevant excerpt
        "url": None
    }
    
    rag_engine.chunks.insert(0, new_chunk)
    rag_engine.build_index()

    return {
        "status": "success",
        "filename": file.filename,
        "chars_extracted": len(extracted_text),
        "message": f"Successfully indexed '{file.filename}'. You can now ask questions about your uploaded document!"
    }

