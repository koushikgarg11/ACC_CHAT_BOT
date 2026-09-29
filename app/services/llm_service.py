"""
Unified Multi-Model LLM Service for Analytics Career Connect AI Chatbot.
Supports:
1. Built-in Local ACC Knowledge Synthesizer (Instant, accurate, zero-cost, offline-capable)
2. Google Gemini API (Gemini 2.0 Flash / 1.5 Flash)
3. OpenAI API (GPT-4o / GPT-4o-mini)
4. Groq API (Llama 3.3 70B / Mixtral)
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# System prompt for all cloud LLMs
SYSTEM_PROMPT = """You are the official AI Assistant for Analytics Career Connect (ACC) - Building Job Ready Tech Talent.
Your job is to provide accurate, helpful, friendly, and structured guidance to students, graduates, and professionals inquiring about ACC's training programs, internships, job assistance, and career opportunities.

Always base your answers on the provided context retrieved from ACC official documents (PDFs) and the company website (https://analyticscareerconnect.com/).

Key Company Facts to Remember:
1. Company Name: Analytics Career Connect (ACC)
2. Tagline: Building Job Ready Tech Talent
3. Founders: Mr. Wasim Patwari (CEO/Founder) & Mrs. Sadaf Khan (Patwari) (Co-Founder)
4. Headquarters: Pune, Maharashtra, India
5. ⚠️ SCAM ALERT POLICY: ACC NEVER charges any fee from college-pursuing students (2027, 2028, 2029 batches) for internships or jobs. All student internships are 100% FREE. Paid programs are only official placement acceleration programs for graduated candidates (2026 & below).
6. Programs:
   - Paid Placement Program With Internship (Data Analytics - 2026 & below graduates / transitioners)
   - Data & Business Analyst Internship (2027, 2028, 2029 Batches - College Students only, 100% Free with performance stipend of ₹5,000-₹10,000/mo)
   - DataYug Project (3 Options: Option 1 General, Option 2 Guided, Option 3 Full Placement)
   - Marketing Internship (Remote, 2/3/4/6 months, 2010-2030 batches)
   - Founder's Office Internship (Strategic, working directly with founders)
   - Job Assistance & Mentorship Program (ATS resume, 1:1 drills, recruiter referrals)
7. Tools Covered: SQL, Power BI, Advanced Excel, Python (Pandas/NumPy), Tableau, DAX, GitHub, Business Analytics.

Formatting Guidelines:
- Use clear markdown formatting (bolding, bullet points, headers).
- Provide actionable next steps and application links when relevant.
- Include a scam alert disclaimer when users ask about internship fees or payments.
- Maintain an encouraging, professional, and transparent tone.
"""

class LLMService:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.preferred_provider = os.getenv("DEFAULT_LLM_PROVIDER", "local") # "local", "gemini", "openai", "groq"

    def set_api_keys(self, gemini_key: Optional[str] = None, openai_key: Optional[str] = None, groq_key: Optional[str] = None):
        """Update runtime API keys."""
        if gemini_key:
            self.gemini_key = gemini_key.strip()
        if openai_key:
            self.openai_key = openai_key.strip()
        if groq_key:
            self.groq_key = groq_key.strip()

    def get_status(self) -> Dict[str, Any]:
        """Returns availability status of all LLM backends."""
        return {
            "local_synthesizer": True,
            "gemini_available": bool(self.gemini_key),
            "openai_available": bool(self.openai_key),
            "groq_available": bool(self.groq_key),
            "active_provider": self.preferred_provider
        }

    async def generate_response(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None,
        provider: Optional[str] = None,
        company_profile: Optional[Dict[str, Any]] = None,
        programs: Optional[List[Dict[str, Any]]] = None,
        doc_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Routes query to selected provider or falls back seamlessly to local synthesizer."""
        target_provider = provider or self.preferred_provider

        # Check if requested cloud provider is configured
        if target_provider == "gemini" and self.gemini_key:
            try:
                ans = await self._call_gemini(query, context_chunks, conversation_history, doc_filter)
                return {"answer": ans, "provider": "Google Gemini (gemini-2.0-flash)"}
            except Exception as e:
                print(f"Gemini error: {e}, falling back to local synthesizer")

        elif target_provider == "openai" and self.openai_key:
            try:
                ans = await self._call_openai(query, context_chunks, conversation_history, doc_filter)
                return {"answer": ans, "provider": "OpenAI (gpt-4o)"}
            except Exception as e:
                print(f"OpenAI error: {e}, falling back to local synthesizer")

        elif target_provider == "groq" and self.groq_key:
            try:
                ans = await self._call_groq(query, context_chunks, conversation_history, doc_filter)
                return {"answer": ans, "provider": "Groq (llama-3.3-70b)"}
            except Exception as e:
                print(f"Groq error: {e}, falling back to local synthesizer")

        # Local High-Accuracy Knowledge Synthesizer
        ans = self._local_synthesizer(query, context_chunks, company_profile, programs, doc_filter)
        return {"answer": ans, "provider": "ACC Built-in Smart Knowledge Engine"}

    async def _call_gemini(self, query: str, chunks: List[Dict[str, Any]], history: Optional[List[Dict[str, str]]], doc_filter: Optional[str] = None) -> str:
        """Invokes Google Gemini using official google-genai SDK."""
        from google import genai
        client = genai.Client(api_key=self.gemini_key)
        
        context_text = "\n\n---\n\n".join([
            f"Source: {c.get('source_name')} ({c.get('source_type')})\nTitle: {c.get('title')}\nContent:\n{c.get('content')}"
            for c in chunks
        ])
        
        prompt = f"{SYSTEM_PROMPT}\n\nRELEVANT KNOWLEDGE CONTEXT:\n{context_text}\n\nUSER QUESTION:\n{query}"
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text

    async def _call_openai(self, query: str, chunks: List[Dict[str, Any]], history: Optional[List[Dict[str, str]]]) -> str:
        """Invokes OpenAI GPT-4o."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.openai_key)
        
        context_text = "\n\n---\n\n".join([
            f"Source: {c.get('source_name')}\nContent:\n{c.get('content')}"
            for c in chunks
        ])
        
        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context_text}"}
        ]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": query})
        
        res = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3
        )
        return res.choices[0].message.content

    async def _call_groq(self, query: str, chunks: List[Dict[str, Any]], history: Optional[List[Dict[str, str]]]) -> str:
        """Invokes Groq Llama 3.3 70B."""
        from groq import AsyncGroq
        client = AsyncGroq(api_key=self.groq_key)
        
        context_text = "\n\n---\n\n".join([
            f"Source: {c.get('source_name')}\nContent:\n{c.get('content')}"
            for c in chunks
        ])
        
        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context_text}"}
        ]
        if history:
            for h in history[-4:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": query})
        
        res = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.2
        )
        return res.choices[0].message.content

    def _local_synthesizer(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        company_profile: Optional[Dict[str, Any]] = None,
        programs: Optional[List[Dict[str, Any]]] = None,
        doc_filter: Optional[str] = None
    ) -> str:
        """
        Synthesizes an extensive, high-quality, structured response based on the top matched
        knowledge chunks and ACC program metadata.
        """
        q_lower = query.lower()

        # Check for specific document query / single document filter
        is_doc_summary = any(k in q_lower for k in ["summarize", "key points", "overview of doc", "from document", "about this doc", "in this pdf", "from this pdf"])
        if (doc_filter and doc_filter.lower() != 'all' and chunks) or (is_doc_summary and chunks):
            first_chunk = chunks[0]
            doc_title = first_chunk.get('title', first_chunk.get('source_name', 'Official Document'))
            doc_name = first_chunk.get('source_name', 'Document')
            category = first_chunk.get('category', 'Career Track')
            target_batch = first_chunk.get('target_batch', 'All')

            extracted_bullets = []
            for c in chunks:
                lines = [line.strip() for line in c.get('content', '').split('\n') if len(line.strip()) > 15]
                for l in lines:
                    if l not in extracted_bullets and len(extracted_bullets) < 8:
                        extracted_bullets.append(l)

            bullets_md = "\n".join([f"- {b}" for b in extracted_bullets])

            return (
                f"### 📄 Document Breakdown: {doc_title}\n\n"
                f"- **Source File:** `{doc_name}`\n"
                f"- **Category:** {category}\n"
                f"- **Target Batch / Eligibility:** {target_batch}\n\n"
                f"#### 🔍 Key Extracted Points & Requirements:\n"
                f"{bullets_md}\n\n"
                f"#### 💡 Summary Context:\n"
                f"{chunks[0].get('content', '')[:350]}...\n\n"
                f"---\n"
                f"👉 **Official ACC Next Steps:** You can apply or inquire directly using our official channels at [analyticscareerconnect.com](https://analyticscareerconnect.com/)."
            )

        # 1. Greetings
        if re.match(r'^(hi|hello|hey|greetings|hola|good\s(morning|afternoon|evening))\b', q_lower.strip()):
            return (
                "👋 **Hello and welcome to Analytics Career Connect (ACC)!**\n\n"
                "I am your dedicated AI Career Assistant. I can assist you with everything regarding our programs, including:\n\n"
                "- 🚀 **Paid Placement Program With Internship** (for 2026 & earlier graduates & transitioners)\n"
                "- 🎓 **Data & Business Analyst Internships** (100% Free for 2027, 2028, 2029 college batches)\n"
                "- 📊 **DataYug Project Tracks** (Option 1, Option 2, Option 3)\n"
                "- 💼 **Marketing & Founder's Office Internships**\n"
                "- 🛠️ **Tools & Skills Covered** (SQL, Power BI, Python, Excel, Tableau, DAX)\n"
                "- ⚠️ **Official Scam Alert Policy** & Zero-Fee Verification\n"
                "- 🔗 **Direct Application Forms & Next Steps**\n\n"
                "Feel free to ask a question below or pick one of the quick suggestions!"
            )

        # 2. Scam Alert / Fees / Is it Free / Charges
        if any(w in q_lower for w in ["scam", "fraud", "fake", "fee", "fees", "charge", "payment", "cost", "money", "free or paid"]):
            return (
                "### ⚠️ Official Scam Alert & Fee Policy\n\n"
                "> **IMPORTANT NOTICE FOR COLLEGE STUDENTS:**\n"
                "> **Analytics Career Connect (ACC) DOES NOT charge any fees** from college-pursuing students (2027, 2028, 2029 batches) for internships or jobs.\n\n"
                "**Key Breakdown:**\n"
                "- **College Students (2027, 2028, 2029 Batches):** **100% FREE**. No registration fees, no training fees. Top contributors are eligible for a **₹5,000 to ₹10,000/month performance stipend**.\n"
                "- **Graduates / Career Switchers (2026 & Below Batches):** ACC offers official comprehensive **Placement Acceleration & Mentorship Programs** with complete 1:1 mentoring, ATS resume rebuilding, and recruitment partner connects.\n\n"
                "🚨 **Reporting Fraud:** If anyone demands payment in the name of ACC for a college student internship, please report it immediately to our HR team at `hr@analyticscareerconnect.com`.\n\n"
                "👉 **Official Application Link:** [Apply via Official ACC Form](https://forms.gle/BSdbcdJTr36W4dC3A)"
            )

        # 3. Founders & Company Information
        if any(w in q_lower for w in ["founder", "founded", "who is", "who are", "wasim", "patwari", "sadaf", "owner", "ceo", "about company"]):
            return (
                "### 🏢 About Analytics Career Connect (ACC)\n\n"
                "**Analytics Career Connect (ACC)** is a fast-growing product-based EdTech, IT, and Recruitment services startup headquartered in **Pune, Maharashtra, India**.\n\n"
                "#### 👥 Founders & Leadership:\n"
                "- **Mr. Wasim Patwari** — CEO & Founder\n"
                "- **Mrs. Sadaf Khan (Patwari)** — Co-Founder\n\n"
                "#### 🎯 Mission & Vision:\n"
                "ACC was established with the vision of building **India's most practical and affordable career acceleration ecosystem**. It bridges the gap between academic theory and real-world tech requirements through live industry projects, 1-on-1 mentorship, and direct hiring networks.\n\n"
                "#### 📍 Key Highlights:\n"
                "- **Headquarters:** Pune, Maharashtra, India\n"
                "- **Official Website:** [https://analyticscareerconnect.com/](https://analyticscareerconnect.com/)\n"
                "- **Core Focus Areas:** Data Analytics, Business Analytics, Power BI, SQL, Python, Job Assistance, and Executive Founder's Office roles."
            )

        # 4. Batches 2027, 2028, 2029 (College Students)
        if any(y in q_lower for y in ["2027", "2028", "2029", "college student", "first year", "second year", "third year"]):
            return (
                "### 🎓 Data & Business Analyst Internship (2027, 2028, 2029 Batches)\n\n"
                "This internship is exclusively designed for **currently enrolled college students** to build real-world analytics projects without disrupting college studies.\n\n"
                "#### 📋 Program Overview:\n"
                "- **Eligibility:** Students graduating in **2027, 2028, or 2029** (B.E., B.Tech, BCA, B.Sc, B.Com, MCA, MBA, etc.).\n"
                "- **Mode:** Remote (Full-Time or Part-Time flexible).\n"
                "- **Duration:** 4 to 6 Months.\n"
                "- **Cost:** **100% FREE** (Zero fees for college students).\n"
                "- **Stipend:** Performance-based stipend of **₹5,000 to ₹10,000/month** for top performing contributors.\n\n"
                "#### 🛠️ Skills & Projects Covered:\n"
                "- **Data Extraction & SQL:** Writing queries, joins, filtering, aggregations.\n"
                "- **BI Dashboards:** Microsoft Power BI dashboard design, KPIs, DAX basics.\n"
                "- **Spreadsheets:** Advanced Microsoft Excel (Pivot tables, VLOOKUP/XLOOKUP, index-match).\n"
                "- **Python Basics:** Data manipulation using Pandas & NumPy.\n"
                "- **Deliverables:** Official Internship Experience Letter + Letter of Recommendation (LOR).\n\n"
                "👉 **Direct Apply Link:** [Fill 2027-2029 Application Form](https://forms.gle/BSdbcdJTr36W4dC3A)"
            )

        # 5. Batches 2026 and Below (Placement Program & DataYug)
        if any(y in q_lower for y in ["2026", "graduated", "placement program", "datayug", "job guarantee", "job assistance"]):
            return (
                "### 🚀 Opportunities for 2026 & Below Batches (Graduates & Final Years)\n\n"
                "For candidates graduating in **2026 or earlier** (including career switchers and working professionals), ACC provides dedicated placement tracks:\n\n"
                "#### 1. Paid Placement Program With Internship\n"
                "- **Goal:** Comprehensive career launch until you land an analytics job.\n"
                "- **Key Perks:** 1-on-1 personalized mentorship, live enterprise case studies, portfolio building (GitHub, Tableau Public, NovyPro), ATS resume rebuilding, and direct partner referrals.\n\n"
                "#### 2. DataYug Project (3 Tailored Options):\n"
                "- **Option 1: General Internship** — For candidates with **80%+ practical analytics knowledge** who only need live project execution.\n"
                "- **Option 2: Guided Internship** — For candidates needing skill enrichment combined with hands-on project experience.\n"
                "- **Option 3: Full Placement Program** — For candidates seeking complete placement support, mock interviews, and dedicated hiring connects.\n\n"
                "#### 🛠️ Core Curriculum:\n"
                "| Module | Topics Covered |\n"
                "| --- | --- |\n"
                "| **SQL** | Advanced Queries, CTEs, Window Functions, Stored Procedures, Database Design |\n"
                "| **Power BI** | Data Modeling, Star Schema, DAX, Interactive Executive Dashboards |\n"
                "| **Python** | Pandas, NumPy, Exploratory Data Analysis (EDA), Matplotlib/Seaborn |\n"
                "| **Excel & Tableau** | Advanced Statistical Analysis, What-If Analysis, Storytelling |\n"
                "| **Career Prep** | Mock Technical Rounds, HR Interview Drills, LinkedIn Profile Optimization |\n\n"
                "👉 **Official Apply Link:** [Apply for 2026 Placement Program](https://forms.gle/CkXbVWW1RCvMKF4C9)"
            )

        # 6. Marketing Internship
        if "marketing" in q_lower:
            return (
                "### 📢 Marketing Intern (Remote | Full-Time / Part-Time)\n\n"
                "- **Eligibility:** 2010 – 2030 Batches (Students & Graduates interested in EdTech & growth marketing).\n"
                "- **Duration Options:** 2 / 3 / 4 / 6 Months.\n"
                "- **Work Mode:** 100% Remote.\n"
                "- **Stipend:** Unpaid with **performance-based cash incentives** for top performers.\n\n"
                "#### 🎯 Key Responsibilities:\n"
                "1. **Content & Social Media Growth:** Managing brand outreach on LinkedIn, Instagram, and student communities.\n"
                "2. **Lead Generation:** Driving candidate outreach for ACC's flagship programs.\n"
                "3. **Campus Partnerships:** Coordinating with college clubs, TPOs, and student ambassadors.\n"
                "4. **Brand Strategy:** Crafting campaigns that showcase student success stories and analytics webinars.\n\n"
                "👉 **Apply Form:** [Marketing Application Form](https://forms.gle/CkXbVWW1RCvMKF4C9)"
            )

        # 7. Founder's Office
        if "founder" in q_lower and "office" in q_lower:
            return (
                "### 👔 Founder's Office Internship\n\n"
                "- **Role:** Strategic Executive Intern working directly with **Mr. Wasim Patwari** & **Mrs. Sadaf Khan**.\n"
                "- **Duration:** 3 to 6 Months (Remote / Hybrid).\n"
                "- **Ideal Candidate:** High-energy problem solver with strong communication, business intuition, and entrepreneurial drive.\n\n"
                "#### 🌟 What You Will Do:\n"
                "- Drive zero-to-one business initiatives and expansion strategies.\n"
                "- Handle market research, competitive benchmarking, and operational workflows.\n"
                "- Directly influence product decisions, hiring pipelines, and strategic partnerships.\n\n"
                "👉 **Apply Online:** [ACC Founder's Office Application](https://analyticscareerconnect.com/founders-office/)"
            )

        # 8. Tools / Curriculum / Skills
        if any(w in q_lower for w in ["tool", "skills", "curriculum", "syllabus", "what will i learn", "technologies", "power bi", "sql", "python", "tableau"]):
            return (
                "### 🛠️ Analytics Career Connect Tech Stack & Curriculum\n\n"
                "ACC's curriculum is reverse-engineered from current industry job descriptions to ensure candidates are 100% job-ready:\n\n"
                "1. **SQL & Databases:**\n"
                "   - Data extraction, filtering (`WHERE`, `HAVING`), multi-table `JOIN`s, Subqueries\n"
                "   - Window Functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LEAD`, `LAG`)\n"
                "   - CTEs (Common Table Expressions) and Aggregate functions\n\n"
                "2. **Microsoft Power BI & DAX:**\n"
                "   - Data Transformation with Power Query\n"
                "   - Star Schema & Snowflake Data Modeling\n"
                "   - DAX Measures (`CALCULATE`, `SUMX`, `FILTER`, Time Intelligence)\n"
                "   - Dynamic, interactive KPI reports and Executive Dashboards\n\n"
                "3. **Python for Analytics:**\n"
                "   - Python fundamentals, data structures, and scripting\n"
                "   - Data wrangling and cleaning with `Pandas` and numerical analysis with `NumPy`\n"
                "   - Data visualization with `Matplotlib` and `Seaborn`\n\n"
                "4. **Advanced Microsoft Excel:**\n"
                "   - Complex Nested Formulas, `XLOOKUP`, `INDEX-MATCH`\n"
                "   - Pivot Tables, Slicers, and Automated Dashboard Layouts\n\n"
                "5. **Career & Portfolio Building:**\n"
                "   - Real-world portfolio projects hosted on **GitHub**, **NovyPro**, and **Tableau Public**\n"
                "   - ATS-friendly Resume crafting and LinkedIn branding."
            )

        # 9. Generic Synthesizer using Context Chunks
        if chunks:
            top_contents = []
            for c in chunks[:3]:
                src = c.get('source_name', 'ACC Document')
                text_snip = c.get('content', '')
                if len(text_snip) > 400:
                    text_snip = text_snip[:400] + "..."
                top_contents.append(f"**From {src}:**\n{text_snip}")

            combined_excerpts = "\n\n".join(top_contents)

            return (
                f"### 📖 Analytics Career Connect Information\n\n"
                f"Based on our official company documents and website knowledge base:\n\n"
                f"{combined_excerpts}\n\n"
                f"---\n"
                f"**Need more details?**\n"
                f"- 🌐 Visit the official website: [analyticscareerconnect.com](https://analyticscareerconnect.com/)\n"
                f"- 📝 [Apply for Programs / Internships](https://forms.gle/CkXbVWW1RCvMKF4C9)\n"
                f"- 📩 Contact: `contact@analyticscareerconnect.com`"
            )

        # Default fallback
        return (
            "I couldn't locate specific documentation on that exact phrase, but Analytics Career Connect (ACC) offers comprehensive Data & Business Analytics placement programs (2026 & below), 100% free student internships (2027-2029), Marketing, and Founder's Office tracks.\n\n"
            "Please explore our programs tab or visit [analyticscareerconnect.com](https://analyticscareerconnect.com/) for more info!"
        )

# Global LLM Service instance
llm_service = LLMService()
