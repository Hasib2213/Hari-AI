from bson import ObjectId
from ..db import db
from ..utils.fingerprint import job_fingerprint

async def create(data):
    data["fingerprint"]=job_fingerprint(data["company"],data["title"],data.get("location",""))
    # Upsert by normalized fingerprint: crawl once, update many.
    await db.jobs.update_one(
        {"fingerprint":data["fingerprint"]},
        {"$set":data, "$setOnInsert":{"created_by":"ingestion"}},
        upsert=True
    )
    return await db.jobs.find_one({"fingerprint":data["fingerprint"]})

async def get(job_id):
    if not ObjectId.is_valid(job_id): return None
    return await db.jobs.find_one({"_id":ObjectId(job_id)})

async def search(query="", limit=20):
    filt={}
    if query:
        terms=[x for x in query.lower().split() if x]
        filt={"$or":[
            {"title":{"$regex":"|".join(terms),"$options":"i"}},
            {"company":{"$regex":"|".join(terms),"$options":"i"}},
            {"description":{"$regex":"|".join(terms),"$options":"i"}},
            {"skills":{"$in":terms}}
        ]}
    return await db.jobs.find(filt).sort("created_at",-1).limit(limit).to_list(limit)
