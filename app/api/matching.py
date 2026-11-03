from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from ..repositories import users, jobs
from ..models.schemas import UserProfile, JobCreate
from ..agents.matching import MatchingAgent
from ..services.gemini import GeminiService
from ..utils.serialize import serialize

router = APIRouter(prefix="/api/matching", tags=["matching"])

def contexts(u, j):
    u_clean = {k: v for k, v in u.items() if k != "_id"}
    j_clean = {k: v for k, v in j.items() if k not in {"_id", "created_at", "fingerprint"}}
    return UserProfile(**u_clean), JobCreate(**j_clean)

@router.get("/{user_id}/recommend")
async def recommend(user_id: str, limit: int = Query(20, ge=1, le=50)):
    """
    Dedicated endpoint replicating Jobright.ai /jobs/recommend.
    Uses candidate's parsed target_titles, skills, location, and remote preferences
    to retrieve and rank the best-fit job opportunities with AI explanations.
    """
    if not ObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user id")
    u = await users.get(user_id)
    if not u:
        raise HTTPException(404, "User not found")

    p = UserProfile(**{k: v for k, v in u.items() if k != "_id"})
    raw_jobs = await jobs.find_for_user(p, limit=limit)
    if not raw_jobs:
        return []

    agent = MatchingAgent(GeminiService())
    return await agent.rank_and_explain(p, raw_jobs, top_ai_count=5)

@router.post("/{user_id}/job/{job_id}")
async def score_single(user_id: str, job_id: str):
    if not ObjectId.is_valid(user_id) or not ObjectId.is_valid(job_id):
        raise HTTPException(400, "Invalid user or job id")
    u = await users.get(user_id)
    j = await jobs.get(job_id)
    if not u or not j:
        raise HTTPException(404, "User or job not found")
    p, x = contexts(dict(u), dict(j))
    result = await MatchingAgent(GeminiService()).score(p, x)
    return {"job_id": job_id, **result.model_dump()}

@router.post("/{user_id}/search")
async def search(user_id: str, query: str = "", limit: int = Query(20, ge=1, le=50)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user id")
    u = await users.get(user_id)
    if not u:
        raise HTTPException(404, "User not found")
    p = UserProfile(**{k: v for k, v in u.items() if k != "_id"})

    if query.strip():
        raw_jobs = await jobs.search(query.strip(), limit=min(limit, 50))
    else:
        raw_jobs = await jobs.find_for_user(p, limit=min(limit, 50))

    if not raw_jobs:
        return []

    agent = MatchingAgent(GeminiService())
    return await agent.rank_and_explain(p, raw_jobs, top_ai_count=5)
