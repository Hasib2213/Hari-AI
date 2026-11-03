from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from bson import ObjectId
from datetime import datetime, timezone
from ..db import db
from ..repositories import jobs, users
from ..models.schemas import (
    UserProfile, JobCreate, ParsedResumeProfile,
    OptimizeSectionRequest, OptimizedSectionResponse
)
from ..agents.resume import ResumeAgent
from ..services.gemini import GeminiService
from ..utils.serialize import serialize

router = APIRouter(prefix="/api/resumes", tags=["resumes"])

async def context(user_id, job_id):
    u = await users.get(user_id)
    j = await jobs.get(job_id)
    if not u or not j:
        raise HTTPException(404, "User or job not found")
    p = UserProfile(**{k: v for k, v in u.items() if k != "_id"})
    x = JobCreate(**{k: v for k, v in j.items() if k not in {"_id", "created_at", "fingerprint"}})
    return p, x

@router.post("/{user_id}/upload", response_model=ParsedResumeProfile)
async def upload_resume(
    user_id: str,
    file: UploadFile = File(...),
    auto_update_profile: bool = Query(True, description="Sync parsed skills, summary, and experience to user profile")
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user id")
    user = await users.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "Uploaded file is empty")

    agent = ResumeAgent(GeminiService())
    try:
        parsed = await agent.parse_file(
            file_bytes=file_bytes,
            filename=file.filename or "resume.pdf",
            content_type=file.content_type or "application/pdf"
        )
    except Exception as e:
        raise HTTPException(500, f"Resume parsing failed: {str(e)}")

    # Update user profile with extracted data if enabled
    if auto_update_profile:
        update_data = {}
        if parsed.raw_text:
            update_data["resume_text"] = parsed.raw_text
        if parsed.skills:
            current_skills = user.get("skills", [])
            update_data["skills"] = list(dict.fromkeys(current_skills + parsed.skills))
        if parsed.target_titles:
            current_titles = user.get("target_titles", [])
            update_data["target_titles"] = list(dict.fromkeys(current_titles + parsed.target_titles))
        if parsed.education:
            update_data["education"] = parsed.education
        if parsed.years_experience > 0:
            update_data["years_experience"] = parsed.years_experience
        if parsed.linkedin_url and not user.get("linkedin_url"):
            update_data["linkedin_url"] = parsed.linkedin_url
        if parsed.github_url and not user.get("github_url"):
            update_data["github_url"] = parsed.github_url
        if parsed.phone and not user.get("phone"):
            update_data["phone"] = parsed.phone
        if parsed.location and not user.get("location"):
            update_data["location"] = parsed.location

        if update_data:
            await users.update(user_id, update_data)

    # Save to resumes collection
    resume_record = {
        "user_id": user_id,
        "filename": file.filename,
        "parsed_profile": parsed.model_dump(),
        "created_at": datetime.now(timezone.utc)
    }
    await db.resumes.insert_one(resume_record)

    return parsed

@router.post("/parse-text", response_model=ParsedResumeProfile)
async def parse_raw_text(resume_text: str):
    if not resume_text.strip():
        raise HTTPException(400, "resume_text cannot be empty")
    agent = ResumeAgent(GeminiService())
    try:
        return await agent.parse_file(
            file_bytes=resume_text.encode("utf-8"),
            filename="resume.txt",
            content_type="text/plain"
        )
    except Exception as e:
        raise HTTPException(500, f"Parsing error: {str(e)}")

@router.post("/{user_id}/analyze")
async def analyze(user_id: str, resume_text: str | None = Query(None, description="Optional: resume text to analyze. If empty, uses user's saved resume.")):
    if not resume_text:
        u = await users.get(user_id)
        if u and u.get("resume_text"):
            resume_text = u["resume_text"]
        else:
            raise HTTPException(400, "No resume_text provided and user has no saved resume. Please pass resume_text or upload a resume first.")
    r = await ResumeAgent(GeminiService()).analyze(resume_text)
    return r.model_dump()

@router.post("/{user_id}/custom/{job_id}")
async def custom(user_id: str, job_id: str):
    p, j = await context(user_id, job_id)
    r = await ResumeAgent(GeminiService()).custom(p, j)
    d = r.model_dump()
    d.update({"user_id": user_id, "job_id": job_id, "status": "draft", "created_at": datetime.now(timezone.utc)})
    await db.resumes.insert_one(d)
    return serialize(d)

@router.post("/{user_id}/{resume_id}/approve")
async def approve(user_id: str, resume_id: str):
    if not ObjectId.is_valid(resume_id):
        raise HTTPException(400, "Invalid resume id")
    await db.resumes.update_one(
        {"_id": ObjectId(resume_id), "user_id": user_id},
        {"$set": {"status": "approved", "approved_at": datetime.now(timezone.utc)}}
    )
    return {"approved": True}

@router.post("/{user_id}/ats/{job_id}")
async def ats(user_id: str, job_id: str, resume_text: str | None = Query(None, description="Optional: resume text to check. If empty, uses candidate's saved resume.")):
    p, j = await context(user_id, job_id)
    text = resume_text or p.resume_text
    if not text:
        raise HTTPException(400, "No resume_text provided and candidate profile has no saved resume.")
    r = await ResumeAgent(GeminiService()).ats(text, j)
    return r.model_dump()

@router.post("/{user_id}/cover-letter/{job_id}")
async def cover(user_id: str, job_id: str, instruction: str = ""):
    p, j = await context(user_id, job_id)
    r = await ResumeAgent(GeminiService()).cover(p, j, instruction)
    return r.model_dump()

@router.post("/{user_id}/cover-letter/rewrite")
async def rewrite(user_id: str, letter: str, instruction: str):
    r = await GeminiService().rewrite_cover_letter(letter, instruction)
    return r.model_dump()

@router.post("/optimize-section", response_model=OptimizedSectionResponse)
async def optimize_section(payload: OptimizeSectionRequest):
    """
    Jobright.ai 1-Click "FIX" Engine for work experience sections.
    Takes a candidate's company, role, description, and bullet points,
    identifies urgent/critical weaknesses, and rewrites them using Google's XYZ formula.
    """
    if not payload.bullets and not payload.raw_description:
        raise HTTPException(400, "Please provide bullets or raw_description to optimize.")

    agent = ResumeAgent(GeminiService())
    try:
        return await agent.optimize_section(
            company=payload.company,
            title=payload.title,
            bullets=payload.bullets,
            raw_description=payload.raw_description or "",
            target_role=payload.target_role or ""
        )
    except Exception as e:
        raise HTTPException(500, f"Section optimization failed: {str(e)}")
