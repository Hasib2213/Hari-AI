from fastapi import APIRouter, HTTPException
from ..models.schemas import UserProfile
from ..repositories import users
from ..utils.serialize import serialize
from datetime import datetime, timezone

router=APIRouter(prefix="/api/users",tags=["users"])

@router.post("")
async def create(payload:UserProfile):
    doc=payload.model_dump(); doc["created_at"]=datetime.now(timezone.utc)
    return serialize(await users.create(doc))

@router.get("/{user_id}")
async def get(user_id:str):
    doc=await users.get(user_id)
    if not doc: raise HTTPException(404,"User not found")
    return serialize(doc)

@router.put("/{user_id}")
async def update(user_id:str,payload:UserProfile):
    doc=await users.update(user_id,payload.model_dump())
    if not doc: raise HTTPException(404,"User not found")
    return serialize(doc)
