from fastapi import APIRouter,HTTPException
from bson import ObjectId
from datetime import datetime,timezone
from ..db import db
from ..repositories import jobs,users
from ..models.schemas import UserProfile,JobCreate
from ..agents.resume import ResumeAgent
from ..services.gemini import GeminiService
from ..utils.serialize import serialize

router=APIRouter(prefix="/api/resumes",tags=["resumes"])

async def context(user_id,job_id):
    u=await users.get(user_id); j=await jobs.get(job_id)
    if not u or not j: raise HTTPException(404,"User or job not found")
    p=UserProfile(**{k:v for k,v in u.items() if k!="_id"})
    x=JobCreate(**{k:v for k,v in j.items() if k not in {"_id","created_at","fingerprint"}})
    return p,x

@router.post("/{user_id}/analyze")
async def analyze(user_id:str,resume_text:str):
    r=await ResumeAgent(GeminiService()).analyze(resume_text)
    return r.model_dump()

@router.post("/{user_id}/custom/{job_id}")
async def custom(user_id:str,job_id:str):
    p,j=await context(user_id,job_id)
    r=await ResumeAgent(GeminiService()).custom(p,j)
    d=r.model_dump(); d.update({"user_id":user_id,"job_id":job_id,"status":"draft","created_at":datetime.now(timezone.utc)})
    await db.resumes.insert_one(d)
    return serialize(d)

@router.post("/{user_id}/{resume_id}/approve")
async def approve(user_id:str,resume_id:str):
    if not ObjectId.is_valid(resume_id): raise HTTPException(400,"Invalid resume id")
    await db.resumes.update_one({"_id":ObjectId(resume_id),"user_id":user_id},{"$set":{"status":"approved","approved_at":datetime.now(timezone.utc)}})
    return {"approved":True}

@router.post("/{user_id}/ats/{job_id}")
async def ats(user_id:str,job_id:str,resume_text:str):
    _,j=await context(user_id,job_id)
    r=await ResumeAgent(GeminiService()).ats(resume_text,j)
    return r.model_dump()

@router.post("/{user_id}/cover-letter/{job_id}")
async def cover(user_id:str,job_id:str,instruction:str=""):
    p,j=await context(user_id,job_id)
    r=await ResumeAgent(GeminiService()).cover(p,j,instruction)
    return r.model_dump()

@router.post("/{user_id}/cover-letter/rewrite")
async def rewrite(user_id:str,letter:str,instruction:str):
    r=await GeminiService().rewrite_cover_letter(letter,instruction)
    return r.model_dump()
