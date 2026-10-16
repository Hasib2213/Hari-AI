from fastapi import APIRouter,HTTPException
from bson import ObjectId
from ..db import db
from ..models.schemas import ChatRequest
from ..services.gemini import GeminiService
from ..agents.explore import ExploreAgent
from ..utils.serialize import serialize

router=APIRouter(prefix="/api/agent",tags=["agent"])

@router.post("/chat/{user_id}")
async def chat(user_id:str,payload:ChatRequest):
    if not ObjectId.is_valid(user_id): raise HTTPException(400,"Invalid user id")
    user=await db.users.find_one({"_id":ObjectId(user_id)})
    if not user: raise HTTPException(404,"User not found")
    ai=GeminiService()
    intent,jobs=await ExploreAgent(ai).handle(payload.message)
    await db.conversations.insert_one({"user_id":user_id,"message":payload.message,"intent":intent.model_dump()})
    return {"intent":intent.model_dump(),"jobs":[serialize(x) for x in jobs]}
