from fastapi import APIRouter,HTTPException
from bson import ObjectId
from ..db import db
from ..services.application import enqueue,set_state,public
from ..repositories import users,jobs
from ..automation.browser_agent import BrowserAgent
from ..services.gemini import GeminiService
from ..models.schemas import UserProfile
from ..config import get_settings

router=APIRouter(prefix="/api/applications",tags=["applications"])
browser=BrowserAgent()

@router.post("/{user_id}/queue/{job_id}")
async def queue(user_id:str,job_id:str):
    if not await users.get(user_id) or not await jobs.get(job_id): raise HTTPException(404,"User or job not found")
    return public(await enqueue(user_id,job_id))

@router.get("/{user_id}/queue")
async def get_queue(user_id:str):
    run=await db.application_runs.find_one({"user_id":user_id,"status":{"$in":["queued","running","awaiting_action"]}})
    return public(run) if run else {"queue":[],"jobs_remaining":0,"status":"empty"}

@router.post("/{user_id}/start")
async def start(user_id:str):
    run=await db.application_runs.find_one({"user_id":user_id,"status":"queued"})
    if not run: raise HTTPException(400,"No queued application run")
    return public(await set_state(str(run["_id"]),"generate_resume","running"))

@router.get("/{user_id}/{run_id}")
async def get_run(user_id:str,run_id:str):
    if not ObjectId.is_valid(run_id): raise HTTPException(400,"Invalid run id")
    run=await db.application_runs.find_one({"_id":ObjectId(run_id),"user_id":user_id})
    if not run: raise HTTPException(404,"Run not found")
    return public(run)

@router.post("/{user_id}/{run_id}/resume-approval")
async def resume_approval(user_id:str,run_id:str,approved:bool):
    if not approved: return public(await set_state(run_id,"awaiting_resume_approval","awaiting_action"))
    return public(await set_state(run_id,"analyzing_site","running"))

@router.post("/{user_id}/{run_id}/analyze")
async def analyze(user_id:str,run_id:str,url:str):
    result=await browser.analyze(url)
    await set_state(run_id,"mapping_fields","running",{"application_url":url,"site_analysis":result})
    return result

@router.post("/{user_id}/{run_id}/map-fields")
async def map_fields(user_id:str,run_id:str):
    run=await db.application_runs.find_one({"_id":ObjectId(run_id),"user_id":user_id})
    user=await users.get(user_id)
    if not run or not user: raise HTTPException(404,"Run or user not found")
    profile=UserProfile(**{k:v for k,v in user.items() if k!="_id"})
    fields=run.get("site_analysis",{}).get("fields",[])
    mapped=await GeminiService().map_fields(profile,profile.resume_text,profile.screening_answers,fields)
    await set_state(run_id,"filling_form","running",{"field_mappings":[x.model_dump() for x in mapped.mappings]})
    return mapped.model_dump()

@router.post("/{user_id}/{run_id}/fill")
async def fill(user_id:str,run_id:str,dry_run:bool=True):
    run=await db.application_runs.find_one({"_id":ObjectId(run_id),"user_id":user_id})
    if not run: raise HTTPException(404,"Run not found")
    result=await browser.fill(run["application_url"],run.get("field_mappings",[]),dry_run=dry_run)
    if not result["skipped"]:
        await set_state(run_id,"awaiting_submission_confirmation","awaiting_action")
    return result

@router.post("/{user_id}/{run_id}/submit")
async def submit(user_id:str,run_id:str,confirm:bool=False):
    if not confirm: raise HTTPException(400,"confirm=true required")
    settings=get_settings()
    if not settings.allow_external_application_submit:
        return {"submitted":False,"dry_run":True,"message":"External submission disabled by configuration."}
    run=await db.application_runs.find_one({"_id":ObjectId(run_id),"user_id":user_id})
    if not run: raise HTTPException(404,"Run not found")
    result=await browser.submit(run["application_url"],dry_run=False)
    await db.applications.insert_one({"user_id":user_id,"run_id":run_id,"url":run["application_url"],"result":result})
    await set_state(run_id,"completed","completed",{"submission_result":result})
    return result
