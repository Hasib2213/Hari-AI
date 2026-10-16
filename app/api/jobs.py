from fastapi import APIRouter, HTTPException
from ..models.schemas import JobCreate
from ..repositories import jobs
from ..utils.serialize import serialize
from datetime import datetime, timezone

router=APIRouter(prefix="/api/jobs",tags=["jobs"])

@router.post("")
async def ingest(payload:JobCreate):
    d=payload.model_dump(); d["created_at"]=datetime.now(timezone.utc)
    return serialize(await jobs.create(d))

@router.get("")
async def list_jobs(query:str="",limit:int=20):
    return [serialize(x) for x in await jobs.search(query,min(limit,50))]

@router.get("/{job_id}")
async def get(job_id:str):
    d=await jobs.get(job_id)
    if not d: raise HTTPException(404,"Job not found")
    return serialize(d)
