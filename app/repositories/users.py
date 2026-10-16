from bson import ObjectId
from ..db import db
from ..utils.serialize import serialize

async def create(data):
    r=await db.users.insert_one(data)
    return await db.users.find_one({"_id":r.inserted_id})

async def get(user_id):
    if not ObjectId.is_valid(user_id): return None
    return await db.users.find_one({"_id":ObjectId(user_id)})

async def update(user_id,data):
    if not ObjectId.is_valid(user_id): return None
    await db.users.update_one({"_id":ObjectId(user_id)},{"$set":data})
    return await get(user_id)
