from fastapi import APIRouter, HTTPException
from bson import ObjectId
from ..repositories import users,jobs
from ..models.schemas import UserProfile,JobCreate
from ..agents.matching import MatchingAgent
from ..services.gemini import GeminiService
from ..utils.serialize import serialize

router=APIRouter(prefix="/api/matching",tags=["matching"])

def contexts(u,j):
    u.pop("_id",None); j.pop("_id",None)
    return UserProfile(**u),JobCreate(**{k:v for k,v in j.items() if k not in {"created_at","fingerprint"}})

@router.post("/{user_id}/job/{job_id}")
async def score(user_id:str,job_id:str):
    u=await users.get(user_id); j=await jobs.get(job_id)
    if not u or not j: raise HTTPException(404,"User or job not found")
    p,x=contexts(dict(u),dict(j))
    result=await MatchingAgent(GeminiService()).score(p,x)
    return {"job_id":job_id,**result.model_dump()}

@router.post("/{user_id}/search")
async def search(user_id:str,query:str="",limit:int=20):
    u=await users.get(user_id)
    if not u: raise HTTPException(404,"User not found")
    p=UserProfile(**{k:v for k,v in u.items() if k!="_id"})
    result=[]
    agent=MatchingAgent(GeminiService())
    for raw in await jobs.search(query,min(limit,50)):
        j=JobCreate(**{k:v for k,v in raw.items() if k not in {"_id","created_at","fingerprint"}})
        m=await agent.score(p,j)
        result.append({"job":serialize(raw),"match":m.model_dump()})
    result.sort(key=lambda x:x["match"]["score"],reverse=True)
    return result
