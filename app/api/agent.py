from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from ..db import db
from ..models.schemas import ChatRequest, CopilotChatResponse
from ..services.gemini import GeminiService
from ..agents.explore import ExploreAgent
from ..utils.serialize import serialize

router = APIRouter(prefix="/api/agent", tags=["agent"])

@router.post("/chat/{user_id}", response_model=CopilotChatResponse)
async def chat(user_id: str, payload: ChatRequest):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user id")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    
    agent = ExploreAgent(GeminiService())
    try:
        return await agent.handle_chat(user_id=user_id, message=payload.message)
    except Exception as e:
        raise HTTPException(500, f"Copilot error: {str(e)}")

@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = Query(30, ge=1, le=100)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user id")
    docs = await db.conversations.find({"user_id": user_id}).sort("created_at", 1).limit(limit).to_list(limit)
    return [serialize(x) for x in docs]

@router.delete("/history/{user_id}")
async def clear_history(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user id")
    result = await db.conversations.delete_many({"user_id": user_id})
    return {"cleared": True, "deleted_count": result.deleted_count}
