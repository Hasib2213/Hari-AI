from datetime import datetime, timezone
from bson import ObjectId
from ..db import db

STEPS=["generate_resume","awaiting_resume_approval","analyzing_site",
       "mapping_fields","filling_form","awaiting_submission_confirmation",
       "submitted","completed","failed"]

def now(): return datetime.now(timezone.utc)

async def enqueue(user_id,job_id):
    run=await db.application_runs.find_one({"user_id":user_id,"status":{"$in":["queued","running","awaiting_action"]}})
    if not run:
        r=await db.application_runs.insert_one({"user_id":user_id,"status":"queued","current_step":"queued","queue":[],"created_at":now()})
        run=await db.application_runs.find_one({"_id":r.inserted_id})
    if not any(x["job_id"]==job_id for x in run.get("queue",[])):
        await db.application_runs.update_one({"_id":run["_id"]},{"$push":{"queue":{"job_id":job_id,"status":"queued"}}})
    return await db.application_runs.find_one({"_id":run["_id"]})

async def set_state(run_id, step, status=None, extra=None):
    update={"current_step":step,"updated_at":now()}
    if status: update["status"]=status
    if extra: update.update(extra)
    await db.application_runs.update_one({"_id":ObjectId(run_id)},{"$set":update})
    return await db.application_runs.find_one({"_id":ObjectId(run_id)})

def public(run):
    q=run.get("queue",[])
    remaining=sum(x.get("status") in {"queued","running"} for x in q)
    return {"id":str(run["_id"]),"status":run.get("status"),
            "current_step":run.get("current_step"),
            "jobs_remaining":remaining,"queue":q}
