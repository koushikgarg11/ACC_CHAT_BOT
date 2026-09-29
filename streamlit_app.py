"""
Analytics Career Connect (ACC) - Streamlit AI Assistant & Career Portal
Runs completely standalone using direct Python in-memory service calls
without requiring a FastAPI backend, ASGI wrapper, or HTTP networking.
Includes Detailed Official PDF Deep-Dives, Full Multi-Page Document Reader,
and Dynamic Multi-File PDF & Document Uploader with Full-Text Semantic Indexing.
"""

import os
import io
import sys
import re
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

import streamlit as st
import pypdf

# Set page configuration
st.set_page_config(
    page_title="Analytics Career Connect | AI Career & Program Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Project paths
WORKSPACE_DIR = os.path.abspath(os.path.dirname(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

DATA_DIR = os.path.join(WORKSPACE_DIR, "app", "data")
KB_FILE = os.path.join(DATA_DIR, "knowledge_base.json")

# Ensure knowledge base exists on disk
if not os.path.exists(KB_FILE):
    from app.knowledge.indexer import build_knowledge_base
    build_knowledge_base()

from app.knowledge.rag_engine import rag_engine
from app.services.llm_service import llm_service
from app.api.chat import generate_followups

# -----------------------------------------------------------------------------
# Custom CSS Styling (Matching ACC Brand Dark Theme & High Contrast)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global App Dark Theme */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #090e1a !important;
        color: #f1f5f9 !important;
    }
    
    header[data-testid="stHeader"] {
        background-color: #090e1a !important;
    }

    /* Sidebar Dark Theme */
    [data-testid="stSidebar"] {
        background-color: #0c1326 !important;
        border-right: 1px solid rgba(56, 189, 248, 0.15) !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebarNav"] {
        background-color: #0c1326 !important;
    }

    /* Header Brand Badge in Sidebar */
    .acc-brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 14px 16px;
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.2), #101a36);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 14px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }
    .acc-logo-box {
        width: 42px;
        height: 42px;
        background: linear-gradient(135deg, #0ea5e9, #2563eb);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff !important;
        font-weight: 800;
        font-size: 1.05rem;
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
        flex-shrink: 0;
    }
    .acc-title-main {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff !important;
        margin: 0;
        line-height: 1.25;
    }
    .acc-tagline {
        font-size: 0.76rem;
        color: #38bdf8 !important;
        margin: 2px 0 0 0;
        font-weight: 500;
    }

    /* Universal Button Styling */
    .stButton > button,
    .stDownloadButton > button,
    button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] {
        background: linear-gradient(135deg, #111c38 0%, #172554 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        padding: 0.5rem 0.85rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    .stButton > button:hover,
    .stDownloadButton > button:hover,
    button[kind="secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        box-shadow: 0 4px 16px rgba(14, 165, 233, 0.45) !important;
        transform: translateY(-1px);
    }
    
    .stButton > button:active,
    .stDownloadButton > button:active {
        transform: translateY(0px);
    }

    /* Primary Form Submit Button */
    .stButton > button[kind="primaryFormSubmit"],
    .stButton > button[kind="primary"],
    button[kind="primary"] {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        box-shadow: 0 4px 14px rgba(14, 165, 233, 0.35) !important;
    }

    /* Link Buttons */
    .stLinkButton > a {
        background: linear-gradient(135deg, #111c38 0%, #1e293b 100%) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        text-align: center !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }
    .stLinkButton > a:hover {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
    }

    /* Chat Messages Styling */
    [data-testid="stChatMessage"] {
        background: #101a36 !important;
        border: 1px solid rgba(56, 189, 248, 0.15) !important;
        border-radius: 14px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: #0d1b38 !important;
        border-color: rgba(14, 165, 233, 0.3) !important;
    }

    /* Chat Input */
    [data-testid="stChatInput"] {
        background-color: #101a36 !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 14px !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
    }

    /* Program & Content Cards */
    .acc-card {
        background: #101a36;
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
    }
    
    /* Badges & Pills */
    .badge-batch {
        background: rgba(14, 165, 233, 0.2);
        color: #38bdf8;
        border: 1px solid rgba(14, 165, 233, 0.4);
        border-radius: 9999px;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-free {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 9999px;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-paid {
        background: rgba(168, 85, 247, 0.2);
        color: #c084fc;
        border: 1px solid rgba(168, 85, 247, 0.4);
        border-radius: 9999px;
        padding: 3px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-scam {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 0.8rem;
        line-height: 1.5;
        margin: 10px 0;
    }

    /* Skill Pill */
    .skill-pill {
        background: rgba(30, 41, 59, 0.9);
        border: 1px solid rgba(71, 85, 105, 0.7);
        color: #cbd5e1;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.72rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
    }

    .domain-pill {
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(14, 165, 233, 0.3);
        color: #7dd3fc;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.72rem;
        font-weight: 500;
        display: inline-block;
        margin-right: 4px;
        margin-bottom: 4px;
    }

    /* Inputs, Selectboxes, and Expanders */
    div[data-baseweb="select"] > div,
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea {
        background-color: #101a36 !important;
        color: #ffffff !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stExpander"] {
        background-color: #101a36 !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Detailed Official Knowledge Metadata (PDFs & Website)
# -----------------------------------------------------------------------------
PDF_CATALOG = [
    {
        "filename": "JD Paid Placement Program With Internship  (1).pdf",
        "title": "Paid Placement Program With Internship (Data Analytics)",
        "subtitle": "100% Placement Support, 1:1 Mentorship & Pay-After-Placement Model",
        "pages": 10,
        "category": "Placement Track",
        "target_batch": "2026 & Below (Graduates, Final Years, Career Switchers)",
        "mode": "Remote (Full-Time / Part-Time) | Mon-Fri (5 Days/Week)",
        "duration": "Up to 3-6 Months (Placement Support until Hired)",
        "fee_model": "Pay-After-Placement: ₹3,000 Registration + ₹2,000 Post-Placement (Total ₹5,000) | 1-Day Free Demo Available",
        "scam_policy": "ACC never charges college pursuing students. Paid programs are only for graduated candidates. Zero hidden fees.",
        "mandatory_tools": ["Microsoft Excel (Advanced)", "SQL (MySQL)", "Python (Pandas / NumPy)", "Power BI", "Tableau"],
        "additional_skills": ["Data Cleaning & Preprocessing", "Exploratory Data Analysis (EDA)", "Business Reporting & Dashboards", "Machine Learning Basics", "Cloud Basics", "Generative AI Tools (ChatGPT, Gemini)"],
        "domains": ["E-commerce", "Retail", "Healthcare", "Banking & Finance", "Marketing & Sales", "Telecom", "Supply Chain", "Hospitality", "Education", "HR Analytics", "Entertainment", "Operations & Reporting"],
        "roles": ["Data Analyst", "Business Intelligence Analyst", "MIS Analyst", "Power BI / Tableau Developer", "Reporting Analyst", "Product Analyst", "Marketing Analyst", "SQL Developer", "Junior Data Scientist", "Data Operations Analyst", "Forecasting Analyst", "BI Consultant", "CRM Data Analyst", "Supply Chain Analyst", "Financial Data Analyst", "Analytics Associate"],
        "highlights": [
            "100% Placement Support until you secure a job (No false guarantee; genuine recruitment partner referrals)",
            "60% Practical Work + 40% Guided Learning across 20+ real-world domain projects",
            "1:1 Mentorship, personalized gap audits, ATS resume rebuilding & LinkedIn optimization",
            "Mock technical and HR interview preparation with corporate work culture simulation",
            "Official Internship Completion Certificate and Experience Letter (No long-term bond/contract)"
        ],
        "apply_url": "https://forms.gle/4NiNQ6PGjUDxWcGM7",
        "contact_number": "9607157409",
        "email": "hr@analyticscareerconnect.com",
        "description": "Comprehensive job description for the paid placement acceleration track. Highlights 100% placement support, 1:1 mentorship, live projects, pay-after-placement model, and scam prevention notice."
    },
    {
        "filename": "Marketing Intern (Remote _ Full-Time _ Part-Time).pdf",
        "title": "Marketing Internship Program",
        "subtitle": "70:30 Learning & Work Culture Model under Founder Leadership",
        "pages": 7,
        "category": "Marketing & Growth",
        "target_batch": "2010 – 2030 (Students, Graduates, Working Professionals, Career Break Candidates)",
        "mode": "Remote | Full-Time (9:00 AM - 6:30 PM, Fri off) or Part-Time (4-5 hrs/day + Full Sunday)",
        "duration": "2, 3, 4, or 6 Months",
        "fee_model": "100% Free / Unpaid Base + Performance-Based Incentives (₹1,000 – ₹5,000+)",
        "scam_policy": "Strict Zero Fee. ACC never charges fees for jobs or internships.",
        "mandatory_tools": ["LinkedIn Marketing & Networking", "Digital Marketing", "Content Creation", "Graphic Designing", "Community Building", "Analytics Reporting"],
        "additional_skills": ["Brand Awareness Campaigns", "Lead Nurturing", "Social Media Storytelling", "Talent Acquisition Support", "Cross-functional Coordination"],
        "domains": ["EdTech Ecosystem", "Startup Operations", "Recruitment Services", "Digital Media", "Student Outreach"],
        "roles": ["Marketing Intern", "Growth Associate", "Brand Strategist", "Social Media Coordinator", "Community Manager", "Talent Acquisition Associate"],
        "highlights": [
            "70% Department-focused marketing & brand growth + 30% Cross-functional exposure (HR, Analytics, Ops)",
            "Direct executive leadership mentorship from Founders Mr. Wasim Patwari and Mrs. Sadaf Khan",
            "Real startup growth campaigns, storytelling, and high-visibility LinkedIn outreach",
            "Performance-based financial incentives and Pre-Placement Offer (PPO) opportunities for top contributors",
            "Official Internship Completion Certificate, Experience Letter, and professional career guidance"
        ],
        "apply_url": "https://forms.gle/wqiMxQ78Rv9dTd9B7",
        "contact_number": "9607157409",
        "email": "hr@analyticscareerconnect.com",
        "description": "Details the remote marketing internship role, founder leadership under Mr. Wasim Patwari and Mrs. Sadaf Khan, performance-based incentives, and 70:30 startup growth responsibilities."
    },
    {
        "filename": "PDF Data &amp; Business Analyst Intern _ Remote] _ 2027_2028_2029 Batch .pdf",
        "title": "Data & Business Analyst Internship (College Students)",
        "subtitle": "100% Free Campus-to-Corporate Program with ₹5K-₹10K Performance Stipends",
        "pages": 13,
        "category": "Student Internship",
        "target_batch": "2027, 2028, 2029 Batches (Currently Enrolled College Students Only)",
        "mode": "Remote (Work From Home) | Part-Time (4-5 hrs/day, Fri off) or Full-Time (9:30 AM - 6:30 PM, Fri-Sat off)",
        "duration": "4 or 6 Months",
        "fee_model": "100% FREE for College Students | Performance-Based KPI Stipend (₹1,000 – ₹10,000/month for top performers)",
        "scam_policy": "Strict Zero-Fee Policy. ACC never charges college students. Report any fee requests to HR immediately.",
        "mandatory_tools": ["Python", "SQL (MySQL)", "Advanced Microsoft Excel", "Power BI", "Tableau", "Web Scraping Fundamentals"],
        "additional_skills": ["Data Cleaning & Preprocessing", "Automated SQL Pipelines", "Predictive Analytics", "EdTech Campaign Analytics", "Talent Sourcing Operations"],
        "domains": ["E-commerce Analytics", "EdTech Vertical", "Talent Acquisition & BPO Hiring", "SaaS Business Metrics"],
        "roles": ["Data Analyst Intern", "Business Analyst Intern", "MIS Intern", "Power BI Developer Intern", "Operations Associate"],
        "highlights": [
            "100% Free practical learning-by-doing program tailored specifically for college students",
            "60% Analytics Work + 40% Startup Cross-functional Exposure (EdTech & Recruitment Verticals)",
            "Structured OJT: Phase 1 (0-90 Days On-the-Job Training) + Phase 2 (Live Project Execution)",
            "Stipend opportunities (₹1K-₹10K) for top KPI contributors after training phase",
            "Verified GitHub portfolio, Letter of Recommendation (LOR) & Certificate",
            "Campus-to-Corporate placement support before graduation"
        ],
        "apply_url": "https://forms.gle/BSdbcdJTr36W4dC3A",
        "contact_number": "9607157409",
        "email": "hr@analyticscareerconnect.com",
        "description": "100% free internship for college students. Covers Excel, SQL, Power BI, Python, performance stipends (₹5K-₹10K), 60:40 startup exposure, official LOR, and scam warnings."
    },
    {
        "filename": "Under DataYug Project Data Analyst JD ( 2026 and Below ) JD (5) (1) (1).pdf",
        "title": "DataYug Project - Data Analyst Opportunities",
        "subtitle": "3 Flexible Career Tracks (Free General Track, Guided Track, or Full Placement)",
        "pages": 10,
        "category": "Placement & Project Tracks",
        "target_batch": "2026 & Earlier Graduates & Final Years",
        "mode": "Remote (Full-Time / Part-Time)",
        "duration": "Flexible 3 to 6 Months",
        "fee_model": "Option 1: 100% Free (for candidates with 80%+ skills) | Option 3: Pay-After-Placement ₹3,000 + ₹2,000",
        "scam_policy": "Transparent track options. No fees for college students. Pay-after-placement only for graduate placement track.",
        "mandatory_tools": ["SQL", "Power BI", "Python (Data Analysis)", "Excel", "Tableau", "Git / GitHub"],
        "additional_skills": ["End-to-End Project Architecture", "KPI Dashboards", "Data Modeling & Star Schema", "Recruiter Technical Showcase"],
        "domains": ["BFSI", "Healthcare", "Supply Chain", "Retail Analytics", "Tech Product Operations"],
        "roles": ["Data Analyst", "Business Analyst", "BI Developer", "Junior Data Engineer"],
        "highlights": [
            "Option 1: General Internship — 100% Free project-focused execution for candidates with 80%+ knowledge",
            "Option 2: Guided Project Track — Structured project mentoring & portfolio validation",
            "Option 3: Full Placement Acceleration — 1:1 mentorship, pay-after-placement, ATS resume & interview referrals",
            "Bridge the gap between theoretical certifications and real-world employer hiring bars",
            "Official certificate, project review badge, and hiring partner introductions"
        ],
        "apply_url": "https://forms.gle/CkXbVWW1RCvMKF4C9",
        "contact_number": "9607157409",
        "email": "hr@analyticscareerconnect.com",
        "description": "Details the 3 specialized tracks: Option 1 (General Internship for 80%+ knowledge), Option 2 (Guided Track), Option 3 (Full Placement Program with pay-after-placement)."
    }
]

WEBSITE_PAGES = [
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

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "custom_uploads" not in st.session_state:
    st.session_state.custom_uploads = []

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

if "selected_doc_scope" not in st.session_state:
    st.session_state.selected_doc_scope = "all"

if "nav_tab" not in st.session_state:
    st.session_state.nav_tab = "💬 AI Career Assistant"

# -----------------------------------------------------------------------------
# Helper Functions (Text Processing, PDF Extraction & Semantic Chunking)
# -----------------------------------------------------------------------------
def resolve_pdf_path(filename: str) -> Optional[str]:
    """Resolves PDF file path across variations of ampersands and paths."""
    candidates = [
        os.path.join(WORKSPACE_DIR, filename),
        os.path.join(WORKSPACE_DIR, filename.replace("&", "&amp;")),
        os.path.join(WORKSPACE_DIR, filename.replace("&amp;", "&"))
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def clean_text_string(text: str) -> str:
    """Normalizes text, removes zero-width characters and duplicate newlines."""
    if not text:
        return ""
    text = re.sub(r'[\u200b\u200c\u200d\uFEFF\xa0]', ' ', text)
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def chunk_text_semantic(text: str, chunk_size: int = 700, chunk_overlap: int = 150) -> List[str]:
    """Splits text into overlapping semantic chunks based on paragraphs."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []
    
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para)
        if current_length + para_len > chunk_size and current_chunk:
            combined = "\n\n".join(current_chunk)
            chunks.append(combined)
            # Retain overlap
            overlap_paras = []
            overlap_len = 0
            for p in reversed(current_chunk):
                if overlap_len + len(p) < chunk_overlap:
                    overlap_paras.insert(0, p)
                    overlap_len += len(p)
                else:
                    break
            current_chunk = overlap_paras
            current_length = sum(len(p) for p in current_chunk)

        current_chunk.append(para)
        current_length += para_len

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks

def extract_document_pages(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Extracts structured page-by-page content from raw bytes (.pdf, .txt, .md)."""
    pages_data = []
    fn_lower = filename.lower()
    
    if fn_lower.endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page_idx, page in enumerate(reader.pages):
                text = clean_text_string(page.extract_text() or "")
                pages_data.append({
                    "page_number": page_idx + 1,
                    "text": text,
                    "char_count": len(text),
                    "word_count": len(text.split())
                })
        except Exception as e:
            st.error(f"Error parsing PDF '{filename}': {e}")
    else:
        # Text or Markdown file
        try:
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            cleaned = clean_text_string(raw_text)
            # Break large text into ~1200 char logical pages
            paragraphs = cleaned.split("\n\n")
            current_page_paras = []
            cur_len = 0
            page_num = 1
            
            for p in paragraphs:
                if cur_len + len(p) > 1200 and current_page_paras:
                    page_str = "\n\n".join(current_page_paras)
                    pages_data.append({
                        "page_number": page_num,
                        "text": page_str,
                        "char_count": len(page_str),
                        "word_count": len(page_str.split())
                    })
                    page_num += 1
                    current_page_paras = [p]
                    cur_len = len(p)
                else:
                    current_page_paras.append(p)
                    cur_len += len(p)
            if current_page_paras:
                page_str = "\n\n".join(current_page_paras)
                pages_data.append({
                    "page_number": page_num,
                    "text": page_str,
                    "char_count": len(page_str),
                    "word_count": len(page_str.split())
                })
        except Exception as e:
            st.error(f"Error parsing text file '{filename}': {e}")
            
    return pages_data

def index_uploaded_document(
    filename: str,
    pages_data: List[Dict[str, Any]],
    category: str,
    target_batch: str,
    raw_bytes: Optional[bytes] = None
) -> int:
    """Indexes all extracted pages of an uploaded document into RAG engine and session state."""
    clean_id_base = re.sub(r'[^a-zA-Z0-9_]', '_', filename)[:16]
    indexed_chunk_count = 0
    total_chars = 0
    created_chunks = []

    for page in pages_data:
        p_num = page["page_number"]
        p_text = page["text"]
        total_chars += page["char_count"]
        
        if not p_text.strip():
            continue

        sub_chunks = chunk_text_semantic(p_text, chunk_size=750, chunk_overlap=120)
        for c_idx, schunk in enumerate(sub_chunks):
            chunk_obj = {
                "id": f"upload_{clean_id_base}_p{p_num}_c{c_idx}",
                "source_type": "User Uploaded Document",
                "source_name": filename,
                "title": f"{filename} (Page {p_num})",
                "category": category,
                "target_batch": target_batch,
                "page": p_num,
                "content": schunk,
                "url": None
            }
            # Add to in-memory RAG engine chunks
            rag_engine.chunks.insert(0, chunk_obj)
            created_chunks.append(chunk_obj)
            indexed_chunk_count += 1

    # Rebuild hybrid BM25 and TF-IDF index
    rag_engine.build_index()

    # Store full metadata in session state
    st.session_state.uploaded_docs[filename] = {
        "filename": filename,
        "title": filename,
        "category": category,
        "target_batch": target_batch,
        "pages": pages_data,
        "total_pages": len(pages_data),
        "chunk_count": indexed_chunk_count,
        "total_chars": total_chars,
        "raw_bytes": raw_bytes,
        "chunks": created_chunks,
        "indexed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if filename not in st.session_state.custom_uploads:
        st.session_state.custom_uploads.append(filename)

    return indexed_chunk_count

def remove_uploaded_document(filename: str):
    """Removes an uploaded document's chunks from the in-memory RAG engine and session state."""
    rag_engine.chunks = [c for c in rag_engine.chunks if c.get("source_name") != filename]
    rag_engine.build_index()
    
    if filename in st.session_state.uploaded_docs:
        del st.session_state.uploaded_docs[filename]
    if filename in st.session_state.custom_uploads:
        st.session_state.custom_uploads.remove(filename)

def get_available_documents() -> List[str]:
    """Returns sorted list of all unique source document names (official + uploaded)."""
    docs = sorted({item.get("source_name", "ACC Document") for item in rag_engine.chunks if item.get("source_name")})
    return ["all"] + docs

def run_chat_query(query: str, doc_filter: str, provider: Optional[str] = None):
    """Executes RAG hybrid search + multi-model LLM generation directly."""
    target_filter = None if doc_filter == "all" else doc_filter
    matched_chunks = rag_engine.search(query, top_k=6, source_filter=target_filter)

    # Citations
    citations = []
    for c in matched_chunks:
        snippet = c.get("content", "")
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        citations.append({
            "id": c.get("id", "c_0"),
            "source_name": c.get("source_name", "ACC Knowledge Base"),
            "source_type": c.get("source_type", "Document"),
            "title": c.get("title", ""),
            "category": c.get("category", "General"),
            "page": c.get("page"),
            "url": c.get("url"),
            "snippet": snippet,
            "relevance_score": c.get("relevance_score", 1.0)
        })

    # History format for LLM
    history_payload = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.chat_messages[-6:]
    ]

    # Generate response
    res = asyncio.run(llm_service.generate_response(
        query=query,
        context_chunks=matched_chunks,
        conversation_history=history_payload,
        provider=provider,
        company_profile=rag_engine.get_company_profile(),
        programs=rag_engine.get_all_programs(),
        doc_filter=target_filter
    ))

    answer = res.get("answer", "")
    provider_name = res.get("provider", "ACC Built-in Smart Knowledge Engine")
    followups = generate_followups(query, answer)

    return answer, provider_name, citations, followups

def evaluate_career_fit(
    graduation_year: int,
    current_skills: List[str],
    knowledge_level: str,
    weekly_hours: int,
    target_role: str
) -> Dict[str, Any]:
    """Calculates optimal program match and roadmap without backend API."""
    skills_lower = [s.lower().strip() for s in current_skills]
    all_programs = rag_engine.get_all_programs()
    
    if target_role == "Marketing / Growth":
        best_program = next((p for p in all_programs if p["id"] == "marketing_internship"), all_programs[0])
        track_title = "Growth & Content Marketing Track"
        cost_status = "100% Free with performance incentives"
        apply_url = "https://forms.gle/CkXbVWW1RCvMKF4C9"
        summary = "Hands-on role focusing on social media growth, lead nurturing, and EdTech brand campaigns."

    elif target_role == "Founder's Office":
        best_program = next((p for p in all_programs if p["id"] == "founders_office_internship"), all_programs[0])
        track_title = "Executive & Strategic Leadership Track"
        cost_status = "Selective strategic internship directly under Founders"
        apply_url = "https://analyticscareerconnect.com/founders-office/"
        summary = "Work directly with Mr. Wasim Patwari and Mrs. Sadaf Khan on scaling operations and strategic partnerships."

    elif graduation_year >= 2027:
        best_program = next((p for p in all_programs if p["id"] == "internship_2027_2029"), all_programs[1])
        track_title = "College Student Data & Business Analyst Internship Track"
        cost_status = "100% FREE for College Students (₹5K-₹10K/mo Performance Stipend available)"
        apply_url = "https://forms.gle/BSdbcdJTr36W4dC3A"
        summary = "Ideal for college students seeking real-world project experience without interrupting semester coursework."

    elif graduation_year <= 2026:
        if "Advanced" in knowledge_level or len([s for s in skills_lower if s in ["sql", "power bi", "python"]]) >= 2:
            best_program = next((p for p in all_programs if p["id"] == "datayug_options_2026"), all_programs[0])
            track_title = "DataYug Project Track (Option 1 / Option 2 - Fast Track)"
            cost_status = "Project-Oriented Fast Track"
            apply_url = "https://forms.gle/CkXbVWW1RCvMKF4C9"
            summary = "Direct industry project execution, data modeling, portfolio validation, and recruiter showcase."
        else:
            best_program = next((p for p in all_programs if p["id"] == "placement_program_2026"), all_programs[0])
            track_title = "ACC Paid Placement Acceleration Program (100% Placement Support)"
            cost_status = "Official Placement Accelerator with 1-on-1 Mentorship & Hiring Partner Referrals"
            apply_url = "https://analyticscareerconnect.com/placement-program/"
            summary = "End-to-end transformation covering SQL, Power BI, Python, ATS resume building, and guaranteed referral support until placed."
    else:
        best_program = all_programs[0]
        track_title = "General Data & Business Analyst Track"
        cost_status = "ACC Career Track"
        apply_url = "https://forms.gle/CkXbVWW1RCvMKF4C9"
        summary = "Comprehensive career support tailored to your analytics goals."

    essential_skills = ["SQL", "Power BI", "Python", "Advanced Excel", "GitHub Portfolio", "Business Case Studies"]
    missing_skills = [s for s in essential_skills if s.lower() not in skills_lower and s.lower().replace(" ", "") not in "".join(skills_lower)]

    roadmap = [
        {"step": 1, "phase": "Foundations", "goal": "Master SQL query optimization, data schemas, and Advanced Excel formulas."},
        {"step": 2, "phase": "Visual Intelligence", "goal": "Build dynamic Power BI & Tableau dashboards with DAX measures and KPI cards."},
        {"step": 3, "phase": "Live Case Studies", "goal": "Execute end-to-end domain projects (E-Commerce, Healthcare, BFSI) and upload to GitHub."},
        {"step": 4, "phase": "Placement & Launch", "goal": "Undergo ATS resume audit, mock technical/HR rounds, and interview scheduling with ACC partner companies."}
    ]

    match_score = min(95, max(30, (len(current_skills) * 15) + (20 if "Intermediate" in knowledge_level else (40 if "Advanced" in knowledge_level else 10))))

    return {
        "recommended_program": best_program,
        "track_title": track_title,
        "cost_status": cost_status,
        "summary": summary,
        "apply_url": apply_url,
        "current_skills": current_skills,
        "missing_skills": missing_skills,
        "match_score": match_score,
        "roadmap": roadmap
    }

# -----------------------------------------------------------------------------
# Sidebar Navigation & Settings
# -----------------------------------------------------------------------------
with st.sidebar:
    st.html("""
    <div class="acc-brand-header">
        <div class="acc-logo-box">ACC</div>
        <div>
            <h1 class="acc-title-main">Analytics Career Connect</h1>
            <p class="acc-tagline">Building Job Ready Tech Talent</p>
        </div>
    </div>
    """)

    nav_options = [
        "💬 AI Career Assistant",
        "🎓 Programs & Job Tracks",
        "🎯 Career Match Calculator",
        "📚 Knowledge & Document Hub",
        "🏢 Company & Scam Policy"
    ]
    
    # Ensure nav_tab exists in session_state
    if st.session_state.nav_tab not in nav_options:
        st.session_state.nav_tab = "💬 AI Career Assistant"
        
    nav_tab = st.radio(
        "Navigation",
        nav_options,
        key="nav_tab",
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Document Scope Filter
    st.markdown("##### 🔍 Document Scope")
    doc_options = get_available_documents()
    if st.session_state.selected_doc_scope not in doc_options:
        st.session_state.selected_doc_scope = "all"

    selected_doc_scope = st.selectbox(
        "Filter answers to specific doc:",
        doc_options,
        key="selected_doc_scope",
        help="Select 'all' to search across all documents and website pages, or choose a specific PDF or custom upload."
    )

    # LLM Provider & Settings
    with st.expander("⚙️ LLM & Engine Settings", expanded=False):
        provider_choice = st.selectbox(
            "Active LLM Engine:",
            ["local", "gemini", "groq", "openai"],
            format_func=lambda x: {
                "local": "⚡ ACC Smart Engine (Built-in)",
                "gemini": "✨ Google Gemini (2.0 Flash)",
                "groq": "🚀 Groq (Llama 3.3 70B)",
                "openai": "🧠 OpenAI (GPT-4o-mini)"
            }.get(x, x)
        )
        llm_service.preferred_provider = provider_choice

        if provider_choice == "gemini":
            gemini_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
            if gemini_key:
                llm_service.set_api_keys(gemini_key=gemini_key)
        elif provider_choice == "groq":
            groq_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
            if groq_key:
                llm_service.set_api_keys(groq_key=groq_key)
        elif provider_choice == "openai":
            openai_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
            if openai_key:
                llm_service.set_api_keys(openai_key=openai_key)

    # Official Scam Alert Notice Badge
    st.html("""
    <div class="badge-scam">
        <strong>🛡️ Official Scam Policy:</strong><br>
        ACC <u>never</u> charges college students (2027-2029) for internships. All college programs are <strong>100% FREE</strong>.
    </div>
    """)

    # Engine Status
    total_chunks = len(rag_engine.chunks)
    custom_count = len(st.session_state.uploaded_docs)
    st.caption(f"🟢 **ACC In-Memory Engine Active** | {total_chunks} Chunks ({custom_count} Custom Docs)")

# -----------------------------------------------------------------------------
# TAB 1: 💬 AI Career Assistant
# -----------------------------------------------------------------------------
if nav_tab == "💬 AI Career Assistant":
    st.markdown("### 💬 ACC Career & Program Advisor")
    st.caption("Document-aware AI Assistant trained on official ACC PDFs, website portals & uploaded documents")

    # Scope indication badge if filtered
    if selected_doc_scope != "all":
        st.info(f"🎯 **Targeted Search Active**: Filtering knowledge scope specifically to `{selected_doc_scope}`. To search everything, switch to 'all' in the sidebar.")

    # Initial Welcome Hero Card (shown when conversation is empty)
    if not st.session_state.chat_messages:
        st.html("""
        <div class="acc-card" style="margin-top: 10px; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.35); background: linear-gradient(135deg, rgba(16, 26, 54, 0.95), rgba(13, 22, 44, 0.95));">
            <div style="display: flex; gap: 16px; align-items: flex-start;">
                <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #0ea5e9, #2563eb); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.3rem; flex-shrink: 0; box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4);">
                    ✨
                </div>
                <div>
                    <h3 style="color: #ffffff; margin: 0 0 6px 0; font-size: 1.15rem; font-weight: 700;">Welcome to Analytics Career Connect!</h3>
                    <p style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.6; margin: 0;">
                        I am your official AI Advisor. I can answer all your questions regarding our <strong>Paid Placement Programs (2026 & Below)</strong>, <strong>100% Free College Internships (2027-2029)</strong>, <strong>DataYug 3 Project Options</strong>, curriculum tools (<em>SQL, Power BI, Python, Excel, Tableau</em>), scam prevention policies, or your uploaded custom documents.
                    </p>
                </div>
            </div>
        </div>
        """)

    # Quick Starter Chips
    st.markdown("##### ⚡ Quick Questions:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🚀 Paid Placement (2026)", use_container_width=True):
            st.session_state.pending_prompt = "Explain the Paid Placement Program for 2026 & below batches in detail."
            st.rerun()
    with col2:
        if st.button("🎓 2027-2029 Free Internship", use_container_width=True):
            st.session_state.pending_prompt = "What are the eligibility and stipend details for 2027, 2028, 2029 batch internships? Is it free?"
            st.rerun()
    with col3:
        if st.button("📊 DataYug (3 Options)", use_container_width=True):
            st.session_state.pending_prompt = "Explain the 3 options under DataYug Project for Data Analysts."
            st.rerun()
    with col4:
        if st.button("⚠️ Scam Policy & Fees", use_container_width=True):
            st.session_state.pending_prompt = "What is ACC's official scam policy regarding fees and internship payments?"
            st.rerun()

    st.markdown("---")

    # Display Chat History
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            
            # Show citations and provider if assistant
            if msg["role"] == "assistant":
                if msg.get("provider"):
                    st.caption(f"_{msg['provider']}_")
                
                citations = msg.get("citations", [])
                if citations:
                    with st.expander(f"📚 View {len(citations)} Verified Citations & References", expanded=False):
                        for cit in citations:
                            page_info = f" | Page {cit['page']}" if cit.get('page') else ""
                            st.markdown(f"**{cit.get('title', 'Reference')}** (`{cit.get('source_name', '')}`{page_info}) — Score: `{cit.get('relevance_score', 1.0)}`")
                            st.markdown(f"> {cit.get('snippet', '')}")

    # Process Pending Prompt or User Input
    user_input = st.chat_input("Ask any question about ACC programs, internships, eligibility, fees, or uploaded documents...")
    
    prompt_to_process = None
    if st.session_state.pending_prompt:
        prompt_to_process = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
    elif user_input:
        prompt_to_process = user_input

    if prompt_to_process:
        st.session_state.chat_messages.append({"role": "user", "content": prompt_to_process})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt_to_process)

        with st.spinner("Searching ACC knowledge chunks & generating guidance..."):
            answer, provider_name, citations, followups = run_chat_query(
                prompt_to_process,
                selected_doc_scope,
                provider=llm_service.preferred_provider
            )

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer,
            "provider": provider_name,
            "citations": citations,
            "followups": followups
        })

        st.rerun()

    # Show Follow-ups for the latest assistant message
    if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "assistant":
        latest_followups = st.session_state.chat_messages[-1].get("followups", [])
        if latest_followups:
            st.markdown("##### 💡 Suggested Follow-ups:")
            f_cols = st.columns(len(latest_followups))
            for idx, q_text in enumerate(latest_followups):
                with f_cols[idx]:
                    if st.button(q_text, key=f"followup_{idx}_{hash(q_text)}", use_container_width=True):
                        st.session_state.pending_prompt = q_text
                        st.rerun()

    # Chat Actions Footer
    if st.session_state.chat_messages:
        st.markdown("---")
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()
        with c2:
            export_text = "\n\n".join([f"**{m['role'].upper()}**: {m['content']}" for m in st.session_state.chat_messages])
            st.download_button(
                "📥 Export Chat",
                data=export_text,
                file_name="ACC_AI_Conversation.md",
                mime="text/markdown",
                use_container_width=True
            )

# -----------------------------------------------------------------------------
# TAB 2: 🎓 Programs & Job Tracks Directory
# -----------------------------------------------------------------------------
elif nav_tab == "🎓 Programs & Job Tracks":
    st.markdown("### 🎓 ACC Programs & Job Descriptions")
    st.caption("Browse all structured training, placement, and internship tracks offered by Analytics Career Connect.")

    # Filter Bar
    f_col1, f_col2 = st.columns([1, 2])
    with f_col1:
        batch_filter = st.selectbox(
            "Target Batch Filter:",
            ["All Batches", "2026 & Below (Graduates / Career Switchers)", "2027, 2028, 2029 (College Students)"]
        )
    with f_col2:
        search_query = st.text_input("🔍 Search by keyword, tool, or role:", placeholder="e.g. Power BI, SQL, Marketing, Free...")

    # Filter programs
    all_programs = rag_engine.get_all_programs()
    filtered_programs = all_programs

    if "2026" in batch_filter:
        filtered_programs = [p for p in filtered_programs if "2026" in p.get("batch", "") or "Earlier" in p.get("batch", "")]
    elif "2027" in batch_filter:
        filtered_programs = [p for p in filtered_programs if "2027" in p.get("batch", "") or "College" in p.get("batch", "")]

    if search_query:
        sq = search_query.lower()
        filtered_programs = [
            p for p in filtered_programs
            if sq in p["title"].lower()
            or sq in p["description"].lower()
            or any(sq in s.lower() for s in p.get("key_skills", []))
        ]

    st.markdown(f"**Showing {len(filtered_programs)} Programs**")

    for prog in filtered_programs:
        with st.container():
            skills_html = ''.join([f'<span class="skill-pill">{s}</span>' for s in prog.get('key_skills', [])])
            st.html(f"""
            <div class="acc-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <h3 style="color: #ffffff; margin: 0 0 6px 0; font-size: 1.15rem;">{prog.get('title')}</h3>
                        <span class="badge-batch">🎯 {prog.get('batch')}</span>
                        <span class="badge-paid" style="margin-left: 6px;">📋 {prog.get('type')}</span>
                    </div>
                    <div>
                        <span style="color: #38bdf8; font-size: 0.85rem; font-weight: 600;">🕒 {prog.get('duration')} | 📍 {prog.get('mode')}</span>
                    </div>
                </div>
                <div style="margin: 12px 0; padding: 10px 14px; background: rgba(14, 165, 233, 0.08); border-left: 3px solid #0ea5e9; border-radius: 6px; font-size: 0.85rem; color: #e2e8f0;">
                    <strong>💰 Cost & Stipend:</strong> {prog.get('stipend')}
                </div>
                <p style="color: #94a3b8; font-size: 0.85rem; line-height: 1.5; margin-bottom: 12px;">{prog.get('description')}</p>
                <div style="margin-bottom: 12px;">
                    <strong style="font-size: 0.8rem; color: #cbd5e1;">🛠️ Key Skills:</strong><br>
                    {skills_html}
                </div>
            </div>
            """)

            # Action Buttons
            b_col1, b_col2, _ = st.columns([1.5, 1.5, 4])
            with b_col1:
                if prog.get('apply_url'):
                    st.link_button("🌐 View Program Page", prog['apply_url'], use_container_width=True)
            with b_col2:
                if prog.get('google_form'):
                    st.link_button("📝 Apply on Google Form", prog['google_form'], use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TAB 3: 🎯 Career Match Calculator
# -----------------------------------------------------------------------------
elif nav_tab == "🎯 Career Match Calculator":
    st.markdown("### 🎯 ACC Career Match Calculator")
    st.caption("Tell us your background and skills to receive an instant fit score, missing skill breakdown, and tailored 4-phase roadmap.")

    with st.form("career_match_form"):
        col1, col2 = st.columns(2)
        with col1:
            grad_year = st.number_input("Graduation Batch / Year:", min_value=2015, max_value=2032, value=2028, step=1)
            target_role = st.selectbox(
                "Target Role:",
                ["Data Analyst", "Business Analyst", "Marketing / Growth", "Founder's Office", "Undecided / Exploring"]
            )
            weekly_hrs = st.slider("Weekly Hours Available:", min_value=5, max_value=45, value=15, step=5)

        with col2:
            knowledge_lvl = st.selectbox(
                "Current Analytics Knowledge Level:",
                ["Beginner (0-30%)", "Intermediate (30-70%)", "Advanced (70-100%)"]
            )
            skills_input = st.multiselect(
                "Current Skills & Tools:",
                ["SQL", "Power BI", "Excel", "Python", "Tableau", "DAX", "Data Modeling", "Git / GitHub", "Statistics", "Communication", "Marketing", "Business Intelligence"],
                default=["SQL", "Excel"]
            )

        submit_btn = st.form_submit_button("🚀 Evaluate My Career Fit & Generate Roadmap", use_container_width=True)

    if submit_btn:
        result = evaluate_career_fit(
            graduation_year=int(grad_year),
            current_skills=skills_input,
            knowledge_level=knowledge_lvl,
            weekly_hours=int(weekly_hrs),
            target_role=target_role
        )

        st.markdown("---")
        st.markdown("### 📊 Your Tailored Match Results")

        # Top Metric Cards
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("🎯 Career Fit Score", f"{result['match_score']}%")
        with m2:
            st.metric("🎓 Recommended Track", result['track_title'])
        with m3:
            st.metric("💳 Cost / Fee Status", result['cost_status'][:30] + "...")

        # Progress bar
        st.progress(result['match_score'] / 100.0)

        # Overview Card
        st.html(f"""
        <div class="acc-card">
            <h4 style="color: #38bdf8; margin: 0 0 8px 0;">📋 Track Summary</h4>
            <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">{result['summary']}</p>
            <div style="margin-top: 10px;">
                <span class="badge-free"><strong>Status:</strong> {result['cost_status']}</span>
            </div>
        </div>
        """)

        # Skill Gap Analysis
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.markdown("##### ✅ Skills You Currently Have:")
            if result['current_skills']:
                for s in result['current_skills']:
                    st.markdown(f"- 🟢 **{s}**")
            else:
                st.caption("No prior tools selected.")

        with s_col2:
            st.markdown("##### 🚀 Recommended Skills to Learn:")
            if result['missing_skills']:
                for s in result['missing_skills']:
                    st.markdown(f"- 🟡 **{s}** (Covered in ACC curriculum)")
            else:
                st.success("You already possess foundational skills! Ready for live project execution.")

        # Tailored 4-Phase Roadmap
        st.markdown("##### 🗺️ Your Tailored 4-Phase ACC Roadmap:")
        for step in result['roadmap']:
            with st.expander(f"Phase {step['step']}: {step['phase']}", expanded=True):
                st.write(f"🎯 **Milestone Goal:** {step['goal']}")

        # Apply Call-to-action
        st.markdown("<br>", unsafe_allow_html=True)
        st.link_button("📝 Apply for This Matched Track Now", result['apply_url'], use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 4: 📚 Knowledge & Document Hub
# -----------------------------------------------------------------------------
elif nav_tab == "📚 Knowledge & Document Hub":
    st.markdown("### 📚 ACC Knowledge & Document Hub")
    st.caption("Explore detailed official PDF job descriptions, search full document transcripts, or upload custom PDF/Docs with semantic indexing for instant AI Q&A.")

    doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
        "📄 Detailed Official PDF Guides",
        "📖 Full Document & Page Reader",
        "📤 Upload New PDF / Custom Docs",
        "🗂️ Manage Uploaded Documents"
    ])

    # -------------------------------------------------------------------------
    # SUB-TAB 1: Detailed Official PDF Guides & Deep Dives
    # -------------------------------------------------------------------------
    with doc_tab1:
        st.markdown("#### 📄 Official ACC PDF Job Descriptions & Deep-Dives")
        st.caption("Complete breakdown of curriculum, eligibility, pay models, project tracks, and scam verification for all 4 official documents.")

        for pdf in PDF_CATALOG:
            tools_html = "".join([f'<span class="skill-pill">{t}</span>' for t in pdf.get("mandatory_tools", [])])
            add_skills_html = "".join([f'<span class="skill-pill" style="border-color:#38bdf8; color:#7dd3fc;">{s}</span>' for s in pdf.get("additional_skills", [])])
            domains_html = "".join([f'<span class="domain-pill">{d}</span>' for d in pdf.get("domains", [])])
            
            with st.expander(f"📄 {pdf['title']} ({pdf['pages']} Pages) — {pdf['target_batch']}", expanded=False):
                st.html(f"""
                <div class="acc-card" style="margin-bottom: 12px; background: rgba(14, 165, 233, 0.05); border: 1px solid rgba(56, 189, 248, 0.3);">
                    <h4 style="color: #38bdf8; margin: 0 0 4px 0;">{pdf['title']}</h4>
                    <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 10px;"><em>{pdf['subtitle']}</em></p>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;">
                        <span class="badge-batch">🎯 {pdf['target_batch']}</span>
                        <span class="badge-paid">📁 {pdf['category']}</span>
                        <span class="badge-free">🕒 {pdf['duration']}</span>
                    </div>
                    <div style="padding: 10px 14px; background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; border-radius: 6px; font-size: 0.85rem; color: #e2e8f0; margin-bottom: 12px;">
                        <strong>💰 Fee & Stipend Model:</strong> {pdf['fee_model']}
                    </div>
                    <p style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.6;">{pdf['description']}</p>
                </div>
                """)

                # Detailed Sections Breakdown
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown("##### 🛠️ Mandatory Tools & Core Tech:")
                    st.html(f"<div>{tools_html}</div>")
                    
                    st.markdown("##### 🚀 Advanced Topics Covered:")
                    st.html(f"<div>{add_skills_html}</div>")

                    st.markdown("##### 🌐 Industry Exposure Domains (12+):")
                    st.html(f"<div>{domains_html}</div>")

                with col_d2:
                    st.markdown("##### 🌟 Key Program Highlights:")
                    for h in pdf.get("highlights", []):
                        st.markdown(f"- ✅ {h}")

                    st.markdown("##### 🛡️ Scam Alert & Zero-Fee Notice:")
                    st.html(f"""
                    <div class="badge-scam" style="margin: 4px 0 10px 0;">
                        {pdf.get('scam_policy', '')}
                    </div>
                    """)

                # Action Bar
                st.markdown("---")
                a_col1, a_col2, a_col3 = st.columns([1.5, 1.5, 2])
                
                # Download original PDF button
                with a_col1:
                    resolved_path = resolve_pdf_path(pdf["filename"])
                    if resolved_path and os.path.exists(resolved_path):
                        with open(resolved_path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button(
                            label=f"📥 Download PDF ({pdf['pages']} Pgs)",
                            data=pdf_bytes,
                            file_name=os.path.basename(resolved_path),
                            mime="application/pdf",
                            key=f"dl_pdf_guide_{hash(pdf['filename'])}",
                            use_container_width=True
                        )
                    else:
                        st.caption("PDF file unavailable")

                # Link button
                with a_col2:
                    if pdf.get("apply_url"):
                        st.link_button("📝 Official Application Form", pdf["apply_url"], use_container_width=True)

                # Ask Question button
                with a_col3:
                    if st.button(f"💬 Ask AI about this PDF", key=f"ask_pdf_{hash(pdf['filename'])}", use_container_width=True):
                        st.session_state.pending_prompt = f"Summarize key eligibility, tools, fee model, and roles for: '{pdf['title']}'."
                        st.session_state.selected_doc_scope = pdf["filename"]
                        st.session_state.nav_tab = "💬 AI Career Assistant"
                        st.rerun()

        st.markdown("#### 🌐 Indexed Official Website Portals")
        w_cols = st.columns(2)
        for idx, page in enumerate(WEBSITE_PAGES):
            with w_cols[idx % 2]:
                st.html(f"""
                <div class="acc-card" style="padding: 12px;">
                    <strong style="color: #38bdf8;">🌐 {page['name']}</strong><br>
                    <span style="font-size: 0.75rem; color: #94a3b8;">{page['topics']}</span><br>
                    <a href="{page['url']}" target="_blank" style="font-size: 0.75rem; color: #0ea5e9;">{page['url']}</a>
                </div>
                """)

    # -------------------------------------------------------------------------
    # SUB-TAB 2: Full Document & Interactive Page Reader
    # -------------------------------------------------------------------------
    with doc_tab2:
        st.markdown("#### 📖 Full Document Content & Interactive Page Reader")
        st.caption("Inspect extracted full text, navigate page-by-page, search keywords, or download any official or uploaded document.")

        # Aggregate available documents for reader
        official_pdf_names = [p["filename"] for p in PDF_CATALOG]
        uploaded_doc_names = list(st.session_state.uploaded_docs.keys())
        all_reader_docs = official_pdf_names + uploaded_doc_names

        selected_reader_doc = st.selectbox(
            "Select Document to Read / Inspect:",
            all_reader_docs,
            index=0,
            help="Choose any official PDF or any uploaded document from your current session."
        )

        doc_pages: List[Dict[str, Any]] = []
        doc_raw_bytes: Optional[bytes] = None
        is_official = selected_reader_doc in official_pdf_names

        if is_official:
            resolved_p = resolve_pdf_path(selected_reader_doc)
            if resolved_p and os.path.exists(resolved_p):
                with open(resolved_p, "rb") as f:
                    doc_raw_bytes = f.read()
                doc_pages = extract_document_pages(doc_raw_bytes, os.path.basename(resolved_p))
        elif selected_reader_doc in st.session_state.uploaded_docs:
            u_info = st.session_state.uploaded_docs[selected_reader_doc]
            doc_pages = u_info.get("pages", [])
            doc_raw_bytes = u_info.get("raw_bytes")

        if not doc_pages:
            st.warning(f"Could not load text for document '{selected_reader_doc}'.")
        else:
            total_doc_pages = len(doc_pages)
            total_doc_chars = sum(p["char_count"] for p in doc_pages)
            total_doc_words = sum(p["word_count"] for p in doc_pages)

            # Metadata header bar
            st.html(f"""
            <div style="display: flex; gap: 16px; flex-wrap: wrap; padding: 10px 14px; background: #101a36; border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; margin-bottom: 14px; font-size: 0.85rem;">
                <div>📄 <strong>Document:</strong> <code>{selected_reader_doc}</code></div>
                <div>📑 <strong>Pages:</strong> {total_doc_pages}</div>
                <div>🔤 <strong>Characters:</strong> {total_doc_chars:,}</div>
                <div>📝 <strong>Words:</strong> {total_doc_words:,}</div>
            </div>
            """)

            # View Mode Selector
            view_mode = st.radio(
                "Reading View Mode:",
                ["📄 Single Page Inspector (with Page Slider)", "📜 Full Document Transcript (All Pages)"],
                horizontal=True
            )

            # Search within Document
            search_term = st.text_input("🔍 Search keyword within this document:", placeholder="e.g. stipend, SQL, refund, scam, placement...")
            if search_term.strip():
                st_kw = search_term.strip().lower()
                matching_pages = [p["page_number"] for p in doc_pages if st_kw in p["text"].lower()]
                if matching_pages:
                    st.success(f"Keyword **'{search_term}'** found on **{len(matching_pages)} page(s)**: {matching_pages}")
                else:
                    st.warning(f"Keyword **'{search_term}'** not found in this document.")

            if view_mode == "📄 Single Page Inspector (with Page Slider)":
                if total_doc_pages > 1:
                    selected_page_num = st.slider("Select Page Number:", min_value=1, max_value=total_doc_pages, value=1)
                else:
                    selected_page_num = 1
                
                cur_page_data = doc_pages[selected_page_num - 1]
                cur_page_text = cur_page_data["text"] or "(No extractable text found on this page)"

                st.markdown(f"##### Page {selected_page_num} Content ({cur_page_data['char_count']} chars, {cur_page_data['word_count']} words):")
                st.text_area(
                    f"Page {selected_page_num} Text",
                    value=cur_page_text,
                    height=380,
                    disabled=True,
                    label_visibility="collapsed"
                )

                # Action row for current page
                r_c1, r_c2 = st.columns([1.5, 3])
                with r_c1:
                    if st.button(f"💬 Ask AI about Page {selected_page_num}", key=f"ask_page_{selected_page_num}", use_container_width=True):
                        st.session_state.pending_prompt = f"Regarding Page {selected_page_num} of '{selected_reader_doc}', what are the key requirements and details mentioned?"
                        st.session_state.selected_doc_scope = selected_reader_doc
                        st.session_state.nav_tab = "💬 AI Career Assistant"
                        st.rerun()

            else:
                # Full document transcript
                full_transcript = "\n\n".join([f"--- [PAGE {p['page_number']}] ---\n\n{p['text']}" for p in doc_pages])
                st.text_area(
                    "Full Document Content",
                    value=full_transcript,
                    height=500,
                    disabled=True,
                    label_visibility="collapsed"
                )

            # Footer Downloads
            st.markdown("---")
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                if doc_raw_bytes:
                    mime_type = "application/pdf" if selected_reader_doc.lower().endswith(".pdf") else "text/plain"
                    st.download_button(
                        label=f"📥 Download Original Document ({selected_reader_doc})",
                        data=doc_raw_bytes,
                        file_name=selected_reader_doc,
                        mime=mime_type,
                        use_container_width=True
                    )
            with d_col2:
                full_text_export = "\n\n".join([f"# Page {p['page_number']}\n\n{p['text']}" for p in doc_pages])
                st.download_button(
                    label="📝 Export Extracted Text as Markdown (.md)",
                    data=full_text_export,
                    file_name=f"{selected_reader_doc}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

    # -------------------------------------------------------------------------
    # SUB-TAB 3: Upload New PDF / Custom Docs with Deep Chunking
    # -------------------------------------------------------------------------
    with doc_tab3:
        st.markdown("#### 📤 Upload PDF & Custom Documents")
        st.caption("Upload candidate resumes, syllabus documents, or custom JD PDFs. Each page is parsed and semantically chunked into the active in-memory RAG knowledge base for immediate AI Assistant Q&A.")

        u_col1, u_col2 = st.columns([2, 1])
        with u_col1:
            uploaded_files = st.file_uploader(
                "Choose one or more files (.pdf, .txt, .md):",
                type=["pdf", "txt", "md"],
                accept_multiple_files=True,
                help="You can upload candidate resumes, course syllabi, job requirements, or corporate documents."
            )

        with u_col2:
            upload_category = st.selectbox(
                "Document Category:",
                ["Candidate Resume / Profile", "Custom Job Description", "Curriculum & Syllabus", "Company Policy / Memo", "General Knowledge"]
            )
            upload_batch = st.selectbox(
                "Target Batch Tag:",
                ["All Batches", "2026 & Below", "2027, 2028, 2029", "Custom"]
            )

        if uploaded_files:
            st.markdown(f"**Selected {len(uploaded_files)} File(s) Ready for Processing:**")
            for uf in uploaded_files:
                st.caption(f"- 📄 `{uf.name}` ({round(len(uf.getvalue())/1024, 1)} KB)")

            if st.button("⚡ Process & Index All Documents into Knowledge Base", type="primary", use_container_width=True):
                with st.spinner("Extracting multi-page text, generating semantic chunks & updating RAG index..."):
                    processed_summary = []
                    for uf in uploaded_files:
                        file_bytes = uf.getvalue()
                        filename = uf.name
                        
                        # Extract pages
                        pages = extract_document_pages(file_bytes, filename)
                        if not pages or not any(p["text"].strip() for p in pages):
                            st.warning(f"Could not extract readable text from '{filename}'.")
                            continue
                        
                        # Index document
                        num_chunks = index_uploaded_document(
                            filename=filename,
                            pages_data=pages,
                            category=upload_category,
                            target_batch=upload_batch,
                            raw_bytes=file_bytes
                        )
                        
                        total_c = sum(p["char_count"] for p in pages)
                        processed_summary.append({
                            "filename": filename,
                            "pages": len(pages),
                            "chunks": num_chunks,
                            "chars": total_c
                        })

                if processed_summary:
                    st.success(f"🎉 Successfully indexed {len(processed_summary)} document(s) into active memory!")
                    
                    for item in processed_summary:
                        st.html(f"""
                        <div class="acc-card" style="margin-top: 10px; border-left: 4px solid #0ea5e9;">
                            <strong style="color: #38bdf8; font-size: 1rem;">✅ {item['filename']}</strong><br>
                            <span style="font-size: 0.85rem; color: #cbd5e1;">
                                📑 <strong>{item['pages']} Pages</strong> | 🧩 <strong>{item['chunks']} Semantic Chunks</strong> | 🔤 <strong>{item['chars']:,} Characters</strong>
                            </span>
                        </div>
                        """)

                    st.markdown("##### 🚀 Test AI with Quick Questions on Your Uploaded Document:")
                    first_uploaded = processed_summary[0]["filename"]
                    q_c1, q_c2, q_c3 = st.columns(3)
                    with q_c1:
                        if st.button(f"📋 Summarize '{first_uploaded[:20]}...'", use_container_width=True):
                            st.session_state.pending_prompt = f"Provide a comprehensive summary of the uploaded document '{first_uploaded}', including main points and requirements."
                            st.session_state.selected_doc_scope = first_uploaded
                            st.session_state.nav_tab = "💬 AI Career Assistant"
                            st.rerun()
                    with q_c2:
                        if st.button(f"🛠️ Extract Key Skills & Tools", use_container_width=True):
                            st.session_state.pending_prompt = f"What are all the technical skills, tools, and qualifications listed in '{first_uploaded}'?"
                            st.session_state.selected_doc_scope = first_uploaded
                            st.session_state.nav_tab = "💬 AI Career Assistant"
                            st.rerun()
                    with q_c3:
                        if st.button(f"🎯 Alignment with ACC Programs", use_container_width=True):
                            st.session_state.pending_prompt = f"How does the profile/document in '{first_uploaded}' align with ACC's Data Analytics placement programs and internships?"
                            st.session_state.selected_doc_scope = first_uploaded
                            st.session_state.nav_tab = "💬 AI Career Assistant"
                            st.rerun()

    # -------------------------------------------------------------------------
    # SUB-TAB 4: Manage Uploaded Documents & Chunks
    # -------------------------------------------------------------------------
    with doc_tab4:
        st.markdown("#### 🗂️ Manage Uploaded Documents & In-Memory Index")
        st.caption("Inspect live in-memory chunks, review document metadata, or remove uploaded documents from the current session.")

        if not st.session_state.uploaded_docs:
            st.info("No custom documents have been uploaded in this session yet. Use the '📤 Upload New PDF / Custom Docs' tab to add documents.")
        else:
            st.markdown(f"**Total Custom Documents in Active Memory: {len(st.session_state.uploaded_docs)}**")

            for fname, info in list(st.session_state.uploaded_docs.items()):
                with st.expander(f"📁 {fname} ({info['total_pages']} Pages, {info['chunk_count']} Chunks) — Indexed at {info.get('indexed_at', 'Now')}", expanded=False):
                    st.markdown(f"- **Category:** {info.get('category')}")
                    st.markdown(f"- **Target Batch:** {info.get('target_batch')}")
                    st.markdown(f"- **Total Characters:** {info.get('total_chars', 0):,}")
                    st.markdown(f"- **Total Chunks in RAG Engine:** {info.get('chunk_count', 0)}")

                    # Chunks preview
                    chunks = info.get("chunks", [])
                    if chunks:
                        st.markdown("##### 🧩 Sample Indexed Chunks:")
                        for idx, ch in enumerate(chunks[:3]):
                            st.caption(f"**Chunk {idx+1} (Page {ch.get('page')})** - ID: `{ch.get('id')}`")
                            st.code(ch.get("content", "")[:280] + "...", language="text")

                    # Actions
                    m_col1, m_col2 = st.columns([1, 4])
                    with m_col1:
                        if st.button(f"🗑️ Delete Document", key=f"del_doc_{hash(fname)}", use_container_width=True):
                            remove_uploaded_document(fname)
                            st.success(f"Removed '{fname}' from knowledge base!")
                            st.rerun()

            st.markdown("---")
            if st.button("🧹 Clear All Uploaded Documents", use_container_width=True):
                for fname in list(st.session_state.uploaded_docs.keys()):
                    remove_uploaded_document(fname)
                st.session_state.uploaded_docs = {}
                st.session_state.custom_uploads = []
                st.success("All custom uploads cleared! Restored official knowledge base.")
                st.rerun()

# -----------------------------------------------------------------------------
# TAB 5: 🏢 Company & Scam Policy
# -----------------------------------------------------------------------------
elif nav_tab == "🏢 Company & Scam Policy":
    st.markdown("### 🏢 Analytics Career Connect (ACC) & Scam Policy")
    st.caption("Official company profile, leadership information, and scam prevention guidelines.")

    company_data = rag_engine.get_company_profile()

    # Company Overview
    st.html(f"""
    <div class="acc-card">
        <h3 style="color: #38bdf8; margin: 0 0 6px 0;">{company_data.get('name', 'Analytics Career Connect')}</h3>
        <p style="color: #0ea5e9; font-weight: 600; font-size: 0.9rem; margin-bottom: 10px;">{company_data.get('tagline', 'Building Job Ready Tech Talent')}</p>
        <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">{company_data.get('description', '')}</p>
        <div style="margin-top: 12px; font-size: 0.85rem; color: #94a3b8;">
            📍 <strong>Headquarters:</strong> {company_data.get('headquarters', 'Pune, Maharashtra, India')}
        </div>
    </div>
    """)

    # Leadership
    st.markdown("#### 👥 Leadership Team")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        st.html("""
        <div class="acc-card">
            <h4 style="color: #ffffff; margin: 0;">Mr. Wasim Patwari</h4>
            <p style="color: #38bdf8; font-size: 0.8rem; margin: 0 0 8px 0;">Founder & CEO</p>
            <p style="color: #94a3b8; font-size: 0.82rem; line-height: 1.4;">Dedicated to making high-impact practical tech education affordable for learners across Tier 1, 2, 3, and 4 cities in India.</p>
        </div>
        """)
    with l_col2:
        st.html("""
        <div class="acc-card">
            <h4 style="color: #ffffff; margin: 0;">Mrs. Sadaf Khan (Patwari)</h4>
            <p style="color: #38bdf8; font-size: 0.8rem; margin: 0 0 8px 0;">Co-Founder</p>
            <p style="color: #94a3b8; font-size: 0.82rem; line-height: 1.4;">Driving student empowerment, operations, community building, and recruitment partner alliances across India.</p>
        </div>
        """)

    # Scam Alert Notice Banner
    st.markdown("#### ⚠️ Official Scam Alert & Verification Policy")
    st.html(f"""
    <div class="badge-scam">
        <h4 style="color: #fbbf24; margin: 0 0 6px 0;">🛡️ Zero-Fee Policy for College Students</h4>
        {company_data.get('official_scam_alert', 'ACC never charges fees from college students.')}
    </div>
    """)

    # Frequently Asked Questions (Accordion)
    st.markdown("#### ❓ Frequently Asked Questions")
    faqs = company_data.get("faqs", [])
    for f in faqs:
        with st.expander(f"❓ {f.get('question')}"):
            st.markdown(f.get('answer'))

    # Contact & Links
    st.markdown("#### 📞 Official Contact & Links")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown("- 🌐 **Website:** [analyticscareerconnect.com](https://analyticscareerconnect.com/)")
        st.markdown("- ✉️ **HR & Verification:** `hr@analyticscareerconnect.com`")
    with c_col2:
        st.markdown("- 📝 **College Internship Form (2027-2029):** [Apply Here](https://forms.gle/BSdbcdJTr36W4dC3A)")
        st.markdown("- 🚀 **Placement Program Form:** [Apply Here](https://forms.gle/CkXbVWW1RCvMKF4C9)")
