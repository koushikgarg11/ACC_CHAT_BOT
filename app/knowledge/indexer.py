"""
Knowledge Base Indexer for Analytics Career Connect (ACC)
Processes PDFs and scraped website data into clean searchable knowledge chunks,
structured program catalogs, and company metadata.
"""

import os
import re
import json
import pypdf

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def clean_text(text: str) -> str:
    """Cleans up raw text, removes zero-width characters and excessive whitespace."""
    if not text:
        return ""
    text = re.sub(r'[\u200b\u200c\u200d\uFEFF\xa0]', ' ', text)
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 700, chunk_overlap: int = 150) -> list[str]:
    """Splits text into overlapping semantic chunks based on paragraphs or sentences."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para)
        if current_length + para_len > chunk_size and current_chunk:
            combined = "\n\n".join(current_chunk)
            chunks.append(combined)
            # Keep overlap
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

def build_knowledge_base():
    """Extracts from PDFs and website data, building structured knowledge chunks."""
    os.makedirs(DATA_DIR, exist_ok=True)
    chunks = []
    
    # 1. Process PDFs
    pdf_files = [
        ("JD Paid Placement Program With Internship  (1).pdf", "Paid Placement Program With Internship (Data Analytics - 2026 & Below)", "Placement Program", "2026 & Below"),
        ("Marketing Intern (Remote _ Full-Time _ Part-Time).pdf", "Marketing Internship Program", "Internship", "2010 - 2030"),
        ("PDF Data &amp; Business Analyst Intern _ Remote] _ 2027_2028_2029 Batch .pdf", "Data & Business Analyst Internship (2027/2028/2029 Batches - Students Only)", "Internship", "2027, 2028, 2029"),
        ("Under DataYug Project Data Analyst JD ( 2026 and Below ) JD (5) (1) (1).pdf", "DataYug Project - Data Analyst Opportunities (2026 & Earlier)", "Project / Placement / Internship", "2026 & Below")
    ]
    
    for filename, title, category, target_batch in pdf_files:
        filepath = os.path.join(WORKSPACE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File {filepath} not found.")
            continue
            
        reader = pypdf.PdfReader(filepath)
        doc_full_text = ""
        page_texts = []
        for page_num, page in enumerate(reader.pages):
            p_text = clean_text(page.extract_text() or "")
            page_texts.append((page_num + 1, p_text))
            doc_full_text += f"\n\n[Page {page_num + 1}]\n" + p_text
            
        # Create chunk per page or sub-chunk
        for page_num, p_text in page_texts:
            if not p_text.strip():
                continue
            sub_chunks = chunk_text(p_text, chunk_size=800, chunk_overlap=120)
            for idx, schunk in enumerate(sub_chunks):
                chunks.append({
                    "id": f"pdf_{filename[:10]}_p{page_num}_c{idx}",
                    "source_type": "PDF Document",
                    "source_name": filename,
                    "title": f"{title} (Page {page_num})",
                    "category": category,
                    "target_batch": target_batch,
                    "page": page_num,
                    "content": schunk,
                    "url": None
                })
        print(f"Indexed PDF: {filename} ({len(reader.pages)} pages)")

    # 2. Process Scraped Website Pages
    web_file = os.path.join(WORKSPACE_DIR, "website_data.json")
    if os.path.exists(web_file):
        with open(web_file, "r", encoding="utf-8") as f:
            web_data = json.load(f)
            
        for url, data in web_data.items():
            name = data.get("name", "Page")
            title = data.get("title", name)
            content = clean_text(data.get("content", ""))
            
            sub_chunks = chunk_text(content, chunk_size=750, chunk_overlap=150)
            for idx, schunk in enumerate(sub_chunks):
                chunks.append({
                    "id": f"web_{name.replace(' ', '_').lower()}_c{idx}",
                    "source_type": "Official Website",
                    "source_name": f"Analytics Career Connect - {name}",
                    "title": f"Website: {title}",
                    "category": "Company & Programs",
                    "target_batch": "All",
                    "page": None,
                    "content": schunk,
                    "url": url
                })
        print(f"Indexed Website: {len(web_data)} pages")

    # 3. Save Knowledge Base
    kb_path = os.path.join(DATA_DIR, "knowledge_base.json")
    with open(kb_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"Total knowledge chunks indexed: {len(chunks)} -> Saved to {kb_path}")

    # 4. Generate Curated Structured Programs Catalog
    programs = [
        {
            "id": "placement_program_2026",
            "title": "Paid Placement Program With Internship (Data Analytics)",
            "batch": "2026 & Below (Graduates / Career Transitioners / Final Years)",
            "type": "Placement Acceleration & Mentorship",
            "mode": "Remote (Full-Time / Part-Time)",
            "duration": "4 to 6 Months (with placement support until hired)",
            "stipend": "Full-Time Placement Support (Paid Program for Graduates with Job Guarantee Assistance)",
            "apply_url": "https://analyticscareerconnect.com/placement-program/",
            "google_form": "https://forms.gle/CkXbVWW1RCvMKF4C9",
            "key_skills": ["SQL (Advanced Queries, Joins, Window Functions)", "Power BI / DAX Dashboards", "Python for Data Analysis (Pandas, NumPy)", "Excel (Pivot Tables, Advanced Formulas)", "Tableau", "Business Analytics Case Studies", "GitHub Portfolio", "Resume & LinkedIn Optimization", "Mock Technical & HR Interviews"],
            "description": "Comprehensive job-ready data analytics program with 1:1 mentorship, live corporate projects, resume reviews, technical mock interviews, and guaranteed recruitment partner referrals until placed.",
            "eligibility": "Graduates of 2026, 2025, 2024 and earlier batches. Working professionals seeking a switch to Data/Business Analytics. No prior coding prerequisites required.",
            "highlights": [
                "100% Placement Support with hiring partner connections",
                "Live End-to-End Analytics Projects (Finance, E-commerce, Healthcare, Sales)",
                "Personalized 1-on-1 Mentorship from Senior Industry Analysts",
                "Portfolio Building on GitHub, Tableau Public & NovyPro",
                "Scam-Free Official Career Accelerator"
            ]
        },
        {
            "id": "internship_2027_2029",
            "title": "Data & Business Analyst Internship (College Students Only)",
            "batch": "2027, 2028, 2029 Batches (Currently Enrolled College Students)",
            "type": "Student Internship",
            "mode": "Remote (Full-Time or Part-Time flexible with college)",
            "duration": "4 to 6 Months",
            "stipend": "100% Free / Unpaid for students (Performance-Based Stipend of ₹5,000 - ₹10,000/month for top contributors)",
            "apply_url": "https://analyticscareerconnect.com/intern/",
            "google_form": "https://forms.gle/BSdbcdJTr36W4dC3A",
            "key_skills": ["Excel & Advanced Formulas", "SQL & Database Queries", "Power BI Dashboards & Visualizations", "Python Data Analytics basics", "Problem Solving & Case Studies"],
            "description": "Exclusively designed for college students to gain practical industry exposure, build real analytics projects, earn verified experience letters, and receive performance stipends.",
            "eligibility": "Currently enrolled students from 2027, 2028, 2029 batches. 100% FREE - ACC NEVER charges college students any fee!",
            "highlights": [
                "100% Free enrollment for college students",
                "Official Internship Certificate & Letter of Recommendation (LOR)",
                "Flexible hours to accommodate college coursework & exams",
                "Performance-based stipend (₹5K - ₹10K) for top contributors",
                "Direct pathway to full placement acceleration upon graduation"
            ]
        },
        {
            "id": "datayug_options_2026",
            "title": "DataYug Project - Data Analyst Track (3 Options)",
            "batch": "2026 & Earlier Batches",
            "type": "Customizable Career / Project Tracks",
            "mode": "Remote",
            "duration": "3 to 6 Months",
            "stipend": "Varies by Option (Direct Placement Track vs Free Internship vs Guided Track)",
            "apply_url": "https://analyticscareerconnect.com/program/",
            "google_form": "https://forms.gle/CkXbVWW1RCvMKF4C9",
            "key_skills": ["SQL", "Power BI", "Python", "Data Cleaning", "Data Modeling", "Business Intelligence", "Stakeholder Communication"],
            "description": "Tailored options based on candidate skill level: Option 1 for candidates with 80%+ ready knowledge needing project experience; Option 2 for guided learning; Option 3 for full placement assistance.",
            "eligibility": "2026 and earlier graduates / final year students.",
            "highlights": [
                "Option 1: General Internship (Fast-track project execution for skilled candidates)",
                "Option 2: Guided Internship (Skill enrichment + project execution)",
                "Option 3: Full Placement Program (Complete placement support + mentorship)"
            ]
        },
        {
            "id": "marketing_internship",
            "title": "Marketing Intern (Learning + Execution + Growth)",
            "batch": "2010 to 2030 Batches (Open to All Enthusiasts)",
            "type": "Marketing & Growth Internship",
            "mode": "Remote (Full-Time / Part-Time)",
            "duration": "2 / 3 / 4 / 6 Months Options",
            "stipend": "Unpaid with Performance-Based Incentives & Stipends for top performers",
            "apply_url": "https://analyticscareerconnect.com/careerpage/",
            "google_form": "https://forms.gle/CkXbVWW1RCvMKF4C9",
            "key_skills": ["Content Marketing", "Social Media Growth (LinkedIn, Instagram)", "Lead Generation & Outreach", "Brand Strategy", "Community Engagement"],
            "description": "Hands-on marketing role within ACC's fast-growing EdTech ecosystem. Gain exposure to digital growth campaigns, lead nurturing, and startup operations.",
            "eligibility": "Students or graduates passionate about marketing, social media, communications, and startup growth.",
            "highlights": [
                "Certificate of Completion & Letter of Recommendation",
                "Performance-based growth and cash incentives",
                "Mentorship from marketing leaders",
                "Practical experience building an EdTech brand"
            ]
        },
        {
            "id": "founders_office_internship",
            "title": "Founder's Office Internship",
            "batch": "College Students & High-Energy Graduates",
            "type": "Executive & Strategic Internship",
            "mode": "Remote / Hybrid",
            "duration": "3 to 6 Months",
            "stipend": "Performance-based rewards + High visibility recommendation",
            "apply_url": "https://analyticscareerconnect.com/founders-office/",
            "google_form": "https://forms.gle/CkXbVWW1RCvMKF4C9",
            "key_skills": ["Strategic Planning", "Startup Operations", "Market Research", "Cross-functional Coordination", "Business Development"],
            "description": "Work directly alongside the founders (Mr. Wasim Patwari & Mrs. Sadaf Khan) on core strategic initiatives, partnerships, growth campaigns, and product operations.",
            "eligibility": "Ambitious individuals with exceptional problem-solving skills, leadership, and drive.",
            "highlights": [
                "Direct 1-on-1 mentorship with the Founders",
                "Unmatched exposure to EdTech startup scaling and leadership",
                "Direct involvement in high-stakes business decisions"
            ]
        },
        {
            "id": "job_assistance_program",
            "title": "ACC Job Assistance & Career Mentorship Program",
            "batch": "All Job Seekers in Data & Tech",
            "type": "Mentorship & Job Assistance",
            "mode": "Online / 1-on-1",
            "duration": "Ongoing until placed",
            "stipend": "Job Search Support",
            "apply_url": "https://analyticscareerconnect.com/job-assistance-program/",
            "google_form": "https://forms.gle/CkXbVWW1RCvMKF4C9",
            "key_skills": ["ATS Resume Rebuilding", "LinkedIn Personal Branding", "Cold Outreach Strategies", "Interview Q&A Drills", "Salary Negotiation"],
            "description": "Targeted career acceleration for candidates who already possess technical skills but need aggressive job search support, portfolio refinement, and direct hiring referrals.",
            "eligibility": "Anyone actively searching for Data Analyst, Business Analyst, or BI Analyst roles.",
            "highlights": [
                "Custom ATS-optimized Resume & Portfolio review",
                "Weekly mock interviews and personalized feedback",
                "Referrals to ACC partner companies and recruiter networks"
            ]
        }
    ]

    programs_path = os.path.join(DATA_DIR, "programs_catalog.json")
    with open(programs_path, "w", encoding="utf-8") as f:
        json.dump(programs, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(programs)} structured programs to {programs_path}")

    # 5. Generate Company Profile & FAQs
    company_profile = {
        "name": "Analytics Career Connect (ACC)",
        "tagline": "Building Job Ready Tech Talent",
        "description": "Analytics Career Connect (ACC) is a premier product-based EdTech, IT, and Recruitment services startup headquartered in Pune, Maharashtra. ACC focuses on bridging the gap between academic education and real-world tech industry expectations through practical, hands-on data analytics training, live projects, 1-on-1 mentorship, and placement acceleration.",
        "founders": {
            "ceo_founder": "Mr. Wasim Patwari",
            "co_founder": "Mrs. Sadaf Khan (Patwari)"
        },
        "headquarters": "Pune, Maharashtra, India",
        "website": "https://analyticscareerconnect.com/",
        "official_scam_alert": "⚠️ SCAM ALERT: Analytics Career Connect (ACC) DOES NOT charge any fee or payment from currently enrolled college students for internships or jobs. All internships for college-going students (e.g., 2027, 2028, 2029 batches) are 100% FREE. Only official comprehensive career placement acceleration programs for graduated candidates are paid. Anyone requesting money from college students in the name of ACC should be reported immediately to the HR department.",
        "core_domains": ["Data Analytics", "Business Analytics", "Business Intelligence (BI)", "Marketing & Growth", "Founders Office Strategy"],
        "core_tech_stack": ["SQL", "Power BI", "Python (Pandas, NumPy, Matplotlib)", "Advanced Excel", "Tableau", "DAX", "Data Modeling", "Git/GitHub", "Statistics"],
        "contact": {
            "website": "https://analyticscareerconnect.com/contact-us/",
            "email": "contact@analyticscareerconnect.com / hr@analyticscareerconnect.com",
            "application_form": "https://forms.gle/CkXbVWW1RCvMKF4C9",
            "internship_form_2027_2029": "https://forms.gle/BSdbcdJTr36W4dC3A"
        },
        "faqs": [
            {
                "question": "Is the internship free or paid for college students?",
                "answer": "All internships for college students (2027, 2028, 2029 batches) are 100% FREE. ACC never charges college students. Top performing interns are eligible for performance-based stipends of ₹5,000 to ₹10,000 per month."
            },
            {
                "question": "Who is eligible for the Placement Program?",
                "answer": "Graduates from 2026, 2025, 2024 and earlier batches, as well as career switchers looking to enter Data and Business Analytics roles with complete placement support and mentorship."
            },
            {
                "question": "What is the DataYug Project?",
                "answer": "DataYug is ACC's specialized industry-simulation project providing 3 distinct tracks for 2026 and earlier candidates: Option 1 (General Internship for skilled candidates with 80%+ knowledge), Option 2 (Guided Internship with skill building), and Option 3 (Full Placement Program)."
            },
            {
                "question": "What tools and skills are taught at Analytics Career Connect?",
                "answer": "The curriculum focuses on high-demand practical tools: SQL (complex queries, window functions, joins), Microsoft Power BI & DAX, Python (Pandas, NumPy, visualization), Advanced Microsoft Excel, Tableau, Business Analytics case studies, and GitHub portfolio creation."
            },
            {
                "question": "Who founded Analytics Career Connect?",
                "answer": "Analytics Career Connect was founded by Mr. Wasim Patwari (CEO/Founder) and Mrs. Sadaf Khan (Patwari) (Co-Founder)."
            },
            {
                "question": "Where is Analytics Career Connect located?",
                "answer": "ACC is headquartered in Pune, Maharashtra, India, and offers remote programs accessible across India and globally."
            }
        ]
    }

    profile_path = os.path.join(DATA_DIR, "company_profile.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(company_profile, f, indent=2, ensure_ascii=False)
    print(f"Saved company profile and FAQs to {profile_path}")

if __name__ == "__main__":
    build_knowledge_base()
