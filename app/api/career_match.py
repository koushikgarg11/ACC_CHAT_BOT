"""
Career Match & Eligibility Calculator API Router.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.knowledge.rag_engine import rag_engine

router = APIRouter(prefix="/api", tags=["Career Match"])

class ProfileEvaluationRequest(BaseModel):
    graduation_year: int
    current_skills: List[str]
    knowledge_level: str # "Beginner (0-30%)", "Intermediate (30-70%)", "Advanced (70-100%)"
    weekly_hours: int
    target_role: str # "Data Analyst", "Business Analyst", "Marketing / Growth", "Founder's Office", "Undecided"

@router.post("/career-match")
async def evaluate_profile(req: ProfileEvaluationRequest):
    year = req.graduation_year
    skills_lower = [s.lower() for s in req.current_skills]
    
    # Analyze Best Program Fit
    all_programs = rag_engine.get_all_programs()
    
    if req.target_role == "Marketing / Growth":
        best_program = next((p for p in all_programs if p["id"] == "marketing_internship"), all_programs[0])
        track_title = "Growth & Content Marketing Track"
        cost_status = "100% Free with performance incentives"
        apply_url = "https://forms.gle/CkXbVWW1RCvMKF4C9"
        summary = "Hands-on role focusing on social media growth, lead nurturing, and EdTech brand campaigns."

    elif req.target_role == "Founder's Office":
        best_program = next((p for p in all_programs if p["id"] == "founders_office_internship"), all_programs[0])
        track_title = "Executive & Strategic Leadership Track"
        cost_status = "Selective strategic internship directly under Founders"
        apply_url = "https://analyticscareerconnect.com/founders-office/"
        summary = "Work directly with Mr. Wasim Patwari and Mrs. Sadaf Khan on scaling operations and strategic partnerships."

    elif year >= 2027:
        best_program = next((p for p in all_programs if p["id"] == "internship_2027_2029"), all_programs[1])
        track_title = "College Student Data & Business Analyst Internship Track"
        cost_status = "100% FREE for College Students (₹5K-₹10K/mo Performance Stipend available)"
        apply_url = "https://forms.gle/BSdbcdJTr36W4dC3A"
        summary = "Ideal for college students seeking real-world project experience without interrupting semester coursework."

    elif year <= 2026:
        # Check skill level for DataYug vs Placement
        if "Advanced" in req.knowledge_level or len([s for s in skills_lower if s in ["sql", "power bi", "python"]]) >= 2:
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

    # Identify Skill Gaps
    essential_skills = ["SQL", "Power BI", "Python", "Advanced Excel", "GitHub Portfolio", "Business Case Studies"]
    missing_skills = [s for s in essential_skills if s.lower() not in skills_lower and s.lower().replace(" ", "") not in "".join(skills_lower)]

    # Roadmap Steps
    roadmap = [
        {"step": 1, "phase": "Foundations", "goal": "Master SQL query optimization, data schemas, and Advanced Excel formulas."},
        {"step": 2, "phase": "Visual Intelligence", "goal": "Build dynamic Power BI & Tableau dashboards with DAX measures and KPI cards."},
        {"step": 3, "phase": "Live Case Studies", "goal": "Execute end-to-end domain projects (E-Commerce, Healthcare, BFSI) and upload to GitHub."},
        {"step": 4, "phase": "Placement & Launch", "goal": "Undergo ATS resume audit, mock technical/HR rounds, and interview scheduling with ACC partner companies."}
    ]

    return {
        "status": "success",
        "recommended_program": best_program,
        "track_title": track_title,
        "cost_status": cost_status,
        "summary": summary,
        "apply_url": apply_url,
        "skill_gap_analysis": {
            "current_skills": req.current_skills,
            "recommended_skills_to_learn": missing_skills,
            "match_score_percentage": min(95, max(30, (len(req.current_skills) * 15) + (20 if "Intermediate" in req.knowledge_level else (40 if "Advanced" in req.knowledge_level else 10))))
        },
        "tailored_roadmap": roadmap
    }
