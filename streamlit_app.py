"""
Analytics Career Connect (ACC) - Streamlit AI Assistant & Career Portal
Runs completely standalone using direct Python in-memory service calls
without requiring a FastAPI backend, ASGI wrapper, or HTTP networking.
"""

import os
import io
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional

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

    /* Universal Button Styling (Fixes washed out white buttons) */
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
# Static Knowledge Metadata (PDFs & Website)
# -----------------------------------------------------------------------------
PDF_CATALOG = [
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
# Session State Setup
# -----------------------------------------------------------------------------
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "custom_uploads" not in st.session_state:
    st.session_state.custom_uploads = []

# -----------------------------------------------------------------------------
# Helper Functions (Direct Python In-Memory Logic)
# -----------------------------------------------------------------------------
def get_available_documents() -> List[str]:
    """Returns sorted unique source document names."""
    docs = sorted({item.get("source_name", "ACC Document") for item in rag_engine.chunks if item.get("source_name")})
    return ["all"] + docs

def run_chat_query(query: str, doc_filter: str, provider: Optional[str] = None):
    """Executes RAG hybrid search + multi-model LLM generation directly."""
    target_filter = None if doc_filter == "all" else doc_filter
    matched_chunks = rag_engine.search(query, top_k=5, source_filter=target_filter)

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
    st.markdown("""
    <div class="acc-brand-header">
        <div class="acc-logo-box">ACC</div>
        <div>
            <h1 class="acc-title-main">Analytics Career Connect</h1>
            <p class="acc-tagline">Building Job Ready Tech Talent</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    nav_tab = st.radio(
        "Navigation",
        [
            "💬 AI Career Assistant",
            "🎓 Programs & Job Tracks",
            "🎯 Career Match Calculator",
            "📚 Knowledge & Document Hub",
            "🏢 Company & Scam Policy"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Document Scope Filter
    st.markdown("##### 🔍 Document Scope")
    doc_options = get_available_documents()
    selected_doc_scope = st.selectbox(
        "Filter answers to specific doc:",
        doc_options,
        index=0,
        help="Select 'all' to search across all documents and website pages, or choose a specific PDF."
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
    st.markdown("""
    <div class="badge-scam">
        <strong>🛡️ Official Scam Policy:</strong><br>
        ACC <u>never</u> charges college students (2027-2029) for internships. All college programs are <strong>100% FREE</strong>.
    </div>
    """, unsafe_allow_html=True)

    # Engine Status
    total_chunks = len(rag_engine.chunks)
    st.caption(f"🟢 **ACC In-Memory Engine Active** | {total_chunks} Chunks Indexed")

# -----------------------------------------------------------------------------
# TAB 1: 💬 AI Career Assistant
# -----------------------------------------------------------------------------
if nav_tab == "💬 AI Career Assistant":
    st.markdown("### 💬 ACC Career & Program Advisor")
    st.caption("Document-aware AI Assistant trained on official ACC PDFs & analyticscareerconnect.com")

    # Initial Welcome Hero Card (shown when conversation is empty)
    if not st.session_state.chat_messages:
        st.markdown("""
        <div class="acc-card" style="margin-top: 10px; margin-bottom: 20px; border: 1px solid rgba(56, 189, 248, 0.35); background: linear-gradient(135deg, rgba(16, 26, 54, 0.95), rgba(13, 22, 44, 0.95));">
            <div style="display: flex; gap: 16px; align-items: flex-start;">
                <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #0ea5e9, #2563eb); display: flex; align-items: center; justify-content: center; color: white; font-size: 1.3rem; flex-shrink: 0; box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4);">
                    ✨
                </div>
                <div>
                    <h3 style="color: #ffffff; margin: 0 0 6px 0; font-size: 1.15rem; font-weight: 700;">Welcome to Analytics Career Connect!</h3>
                    <p style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.6; margin: 0;">
                        I am your official AI Advisor. I can answer all your questions regarding our <strong>Paid Placement Programs (2026 & Below)</strong>, <strong>100% Free College Internships (2027-2029)</strong>, <strong>DataYug 3 Project Options</strong>, curriculum tools (<em>SQL, Power BI, Python, Excel, Tableau</em>), scam prevention policies, and official application links.
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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

    # Process Pending Prompt or Input
    user_input = st.chat_input("Ask any question about ACC programs, internships, eligibility, or fees...")
    
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
            st.markdown(f"""
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
                    {''.join([f'<span class="skill-pill">{s}</span>' for s in prog.get('key_skills', [])])}
                </div>
            </div>
            """, unsafe_allow_html=True)

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
        st.markdown(f"""
        <div class="acc-card">
            <h4 style="color: #38bdf8; margin: 0 0 8px 0;">📋 Track Summary</h4>
            <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">{result['summary']}</p>
            <div style="margin-top: 10px;">
                <span class="badge-free"><strong>Status:</strong> {result['cost_status']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
    st.caption("Explore indexed official PDF job descriptions, website knowledge portals, or upload candidate resumes for immediate in-session Q&A.")

    doc_tab1, doc_tab2, doc_tab3 = st.tabs(["📄 Indexed Official Documents", "📖 PDF Page Reader", "📤 Upload Resume / Custom Doc"])

    # Sub-tab 1: Indexed PDFs & Website Pages
    with doc_tab1:
        st.markdown("#### 📄 Official Indexed PDF Documents")
        for pdf in PDF_CATALOG:
            with st.expander(f"📄 {pdf['title']} ({pdf['pages']} Pages)"):
                st.markdown(f"- **Filename:** `{pdf['filename']}`")
                st.markdown(f"- **Category:** {pdf['category']}")
                st.markdown(f"- **Target Batch:** {pdf['target_batch']}")
                st.markdown(f"- **Summary:** {pdf['description']}")

        st.markdown("#### 🌐 Official Indexed Website Pages")
        w_cols = st.columns(2)
        for idx, page in enumerate(WEBSITE_PAGES):
            with w_cols[idx % 2]:
                st.markdown(f"""
                <div class="acc-card" style="padding: 12px;">
                    <strong style="color: #38bdf8;">🌐 {page['name']}</strong><br>
                    <span style="font-size: 0.75rem; color: #94a3b8;">{page['topics']}</span><br>
                    <a href="{page['url']}" target="_blank" style="font-size: 0.75rem; color: #0ea5e9;">{page['url']}</a>
                </div>
                """, unsafe_allow_html=True)

    # Sub-tab 2: Interactive PDF Page Reader
    with doc_tab2:
        st.markdown("#### 📖 PDF Page Reader & Text Inspector")
        selected_pdf = st.selectbox("Select PDF to inspect:", [p["filename"] for p in PDF_CATALOG])
        
        filepath = os.path.join(WORKSPACE_DIR, selected_pdf)
        if not os.path.exists(filepath):
            alt_path = os.path.join(WORKSPACE_DIR, selected_pdf.replace("&", "&amp;"))
            if os.path.exists(alt_path):
                filepath = alt_path

        if os.path.exists(filepath):
            try:
                reader = pypdf.PdfReader(filepath)
                total_pages = len(reader.pages)
                file_size_kb = round(os.path.getsize(filepath) / 1024, 1)

                st.caption(f"File: `{os.path.basename(filepath)}` | Total Pages: {total_pages} | Size: {file_size_kb} KB")

                page_num = st.slider("Select Page Number:", min_value=1, max_value=total_pages, value=1)
                page_text = reader.pages[page_num - 1].extract_text() or "(No readable text found on this page)"

                st.markdown(f"##### Page {page_num} Content ({len(page_text)} characters):")
                st.text_area(f"Extracted Text (Page {page_num})", value=page_text, height=350, disabled=True)
            except Exception as e:
                st.error(f"Error opening PDF: {e}")
        else:
            st.warning(f"File '{selected_pdf}' not found in workspace.")

    # Sub-tab 3: Upload Candidate Resume / Document
    with doc_tab3:
        st.markdown("#### 📤 Upload Candidate Resume or Custom Document")
        st.caption("Upload a resume or job requirement (.pdf, .txt, .md) to index it directly in-memory for instant AI Assistant Q&A!")

        uploaded_file = st.file_uploader("Choose a file:", type=["pdf", "txt", "md"])
        if uploaded_file is not None:
            extracted_text = ""
            if uploaded_file.name.lower().endswith(".pdf"):
                try:
                    pdf_reader = pypdf.PdfReader(io.BytesIO(uploaded_file.getvalue()))
                    for p in pdf_reader.pages:
                        extracted_text += (p.extract_text() or "") + "\n"
                except Exception as e:
                    st.error(f"Failed to parse uploaded PDF: {e}")
            else:
                extracted_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")

            if extracted_text.strip():
                if st.button("📥 Index Document into In-Memory Knowledge Base"):
                    chunk_id = f"upload_{uploaded_file.name[:8]}"
                    new_chunk = {
                        "id": chunk_id,
                        "source_type": "User Uploaded Document",
                        "source_name": uploaded_file.name,
                        "title": f"Candidate Resume: {uploaded_file.name}",
                        "category": "Candidate Profile",
                        "target_batch": "Custom",
                        "page": 1,
                        "content": extracted_text[:3000],
                        "url": None
                    }
                    rag_engine.chunks.insert(0, new_chunk)
                    rag_engine.build_index()
                    st.session_state.custom_uploads.append(uploaded_file.name)
                    st.success(f"🎉 Successfully indexed '{uploaded_file.name}' ({len(extracted_text)} chars)! You can now ask questions about this document in the AI Assistant tab.")
            else:
                st.warning("Could not extract any text from the uploaded file.")

# -----------------------------------------------------------------------------
# TAB 5: 🏢 Company & Scam Policy
# -----------------------------------------------------------------------------
elif nav_tab == "🏢 Company & Scam Policy":
    st.markdown("### 🏢 Analytics Career Connect (ACC) & Scam Policy")
    st.caption("Official company profile, leadership information, and scam prevention guidelines.")

    company_data = rag_engine.get_company_profile()

    # Company Overview
    st.markdown(f"""
    <div class="acc-card">
        <h3 style="color: #38bdf8; margin: 0 0 6px 0;">{company_data.get('name', 'Analytics Career Connect')}</h3>
        <p style="color: #0ea5e9; font-weight: 600; font-size: 0.9rem; margin-bottom: 10px;">{company_data.get('tagline', 'Building Job Ready Tech Talent')}</p>
        <p style="color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">{company_data.get('description', '')}</p>
        <div style="margin-top: 12px; font-size: 0.85rem; color: #94a3b8;">
            📍 <strong>Headquarters:</strong> {company_data.get('headquarters', 'Pune, Maharashtra, India')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Leadership
    st.markdown("#### 👥 Leadership Team")
    l_col1, l_col2 = st.columns(2)
    with l_col1:
        st.markdown("""
        <div class="acc-card">
            <h4 style="color: #ffffff; margin: 0;">Mr. Wasim Patwari</h4>
            <p style="color: #38bdf8; font-size: 0.8rem; margin: 0 0 8px 0;">Founder & CEO</p>
            <p style="color: #94a3b8; font-size: 0.82rem; line-height: 1.4;">Dedicated to making high-impact practical tech education affordable for learners across Tier 1, 2, 3, and 4 cities in India.</p>
        </div>
        """, unsafe_allow_html=True)
    with l_col2:
        st.markdown("""
        <div class="acc-card">
            <h4 style="color: #ffffff; margin: 0;">Mrs. Sadaf Khan (Patwari)</h4>
            <p style="color: #38bdf8; font-size: 0.8rem; margin: 0 0 8px 0;">Co-Founder</p>
            <p style="color: #94a3b8; font-size: 0.82rem; line-height: 1.4;">Driving student empowerment, operations, community building, and recruitment partner alliances across India.</p>
        </div>
        """, unsafe_allow_html=True)

    # Scam Alert Notice Banner
    st.markdown("#### ⚠️ Official Scam Alert & Verification Policy")
    st.markdown(f"""
    <div class="badge-scam">
        <h4 style="color: #fbbf24; margin: 0 0 6px 0;">🛡️ Zero-Fee Policy for College Students</h4>
        {company_data.get('official_scam_alert', 'ACC never charges fees from college students.')}
    </div>
    """, unsafe_allow_html=True)

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
