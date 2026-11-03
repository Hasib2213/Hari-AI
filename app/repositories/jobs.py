import re
from bson import ObjectId
from ..db import db
from ..utils.fingerprint import job_fingerprint

async def create(data):
    data["fingerprint"] = job_fingerprint(data["company"], data["title"], data.get("location", ""))
    # Upsert by normalized fingerprint: crawl once, update many.
    await db.jobs.update_one(
        {"fingerprint": data["fingerprint"]},
        {"$set": data, "$setOnInsert": {"created_by": "ingestion"}},
        upsert=True
    )
    return await db.jobs.find_one({"fingerprint": data["fingerprint"]})

async def get(job_id):
    if not ObjectId.is_valid(job_id):
        return None
    return await db.jobs.find_one({"_id": ObjectId(job_id)})

async def search(query="", limit=20):
    filt = {}
    if query:
        terms = [x for x in query.lower().split() if x]
        filt = {"$or": [
            {"title": {"$regex": "|".join(terms), "$options": "i"}},
            {"company": {"$regex": "|".join(terms), "$options": "i"}},
            {"description": {"$regex": "|".join(terms), "$options": "i"}},
            {"skills": {"$in": terms}}
        ]}
    return await db.jobs.find(filt).sort("created_at", -1).limit(limit).to_list(limit)

async def find_for_user(profile, limit=30):
    or_clauses = []
    if getattr(profile, "target_titles", None):
        terms = [re.escape(t.strip()) for t in profile.target_titles if t.strip()]
        if terms:
            or_clauses.append({"title": {"$regex": "|".join(terms), "$options": "i"}})
    if getattr(profile, "skills", None):
        lower_skills = [s.strip().lower() for s in profile.skills if s.strip()]
        if lower_skills:
            or_clauses.append({"skills": {"$in": lower_skills}})

    filt = {}
    if or_clauses:
        filt["$or"] = or_clauses
    if getattr(profile, "excluded_companies", None):
        filt["company"] = {"$nin": profile.excluded_companies}
    if getattr(profile, "remote_only", False):
        filt["remote"] = True

    docs = await db.jobs.find(filt).sort("created_at", -1).limit(limit).to_list(limit)
    if len(docs) < 5:
        fallback_filt = {}
        if getattr(profile, "excluded_companies", None):
            fallback_filt["company"] = {"$nin": profile.excluded_companies}
        docs = await db.jobs.find(fallback_filt).sort("created_at", -1).limit(limit).to_list(limit)
    return docs
