from fastapi import APIRouter
from ..db import ping_db
router=APIRouter(tags=["system"])
@router.get("/health")
async def health():
    await ping_db()
    return {"status":"ok"}
