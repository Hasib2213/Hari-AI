from datetime import datetime, timezone
from bson import ObjectId
from ..db import db
from ..services.gemini import GeminiService
from ..models.schemas import (
    InterviewQuestion, QuestionGuide, STAREvaluationResponse, InterviewPracticeRequest
)
from ..repositories import users
from ..utils.serialize import serialize

class InterviewAgent:
    def __init__(self, ai: GeminiService | None = None):
        self.ai = ai or GeminiService()

    async def get_questions(self, company: str = "Google", role: str = "Software Engineer", category: str = "behavioral", limit: int = 10) -> list[dict]:
        query = {"category": category}
        if company and company.lower() != "all":
            query["company"] = {"$regex": f"^{company}$", "$options": "i"}
        if role and role.lower() != "all":
            query["role"] = {"$regex": f"^{role}$", "$options": "i"}

        existing = await db.interview_questions.find(query).limit(limit).to_list(limit)

        if len(existing) < 3 and company.lower() != "all":
            needed = max(5, limit - len(existing))
            try:
                generated = await self.ai.generate_company_questions(company=company, role=role, category=category, count=needed)
                for q in generated.questions:
                    doc = q.model_dump()
                    doc.pop("id", None)
                    doc["created_at"] = datetime.now(timezone.utc)
                    r = await db.interview_questions.insert_one(doc)
                    doc["id"] = str(r.inserted_id)
                    existing.append(doc)
            except Exception as e:
                # If generation fails, return whatever existing questions we have
                pass

        return [serialize(x) for x in existing[:limit]]

    async def get_guide(self, question_id: str | None = None, question_text: str | None = None, company: str = "General", role: str = "Software Engineer") -> dict:
        doc = None
        if question_id and ObjectId.is_valid(question_id):
            doc = await db.interview_questions.find_one({"_id": ObjectId(question_id)})
            if doc:
                question_text = doc.get("question", question_text)
                company = doc.get("company", company)
                role = doc.get("role", role)
                if doc.get("guide"):
                    return doc["guide"]

        if not question_text:
            raise ValueError("question_text or valid question_id is required")

        guide_res = await self.ai.get_question_guide(company=company, role=role, question=question_text)
        guide_dict = guide_res.model_dump()

        if doc and question_id:
            await db.interview_questions.update_one(
                {"_id": ObjectId(question_id)},
                {"$set": {"guide": guide_dict, "updated_at": datetime.now(timezone.utc)}}
            )

        return guide_dict

    async def evaluate_practice(self, payload: InterviewPracticeRequest) -> dict:
        user_profile = None
        if payload.user_id:
            raw_user = await users.get(payload.user_id)
            if raw_user:
                user_profile = {k: v for k, v in raw_user.items() if k != "_id"}

        question_text = payload.question_text
        company = payload.company
        role = payload.role

        if payload.question_id and ObjectId.is_valid(payload.question_id):
            doc = await db.interview_questions.find_one({"_id": ObjectId(payload.question_id)})
            if doc:
                question_text = doc.get("question", question_text)
                company = doc.get("company", company)
                role = doc.get("role", role)

        evaluation = await self.ai.evaluate_star_answer(
            question=question_text,
            company=company,
            role=role,
            candidate_answer=payload.candidate_answer,
            candidate_profile=user_profile
        )

        session_doc = {
            "user_id": payload.user_id,
            "question_id": payload.question_id,
            "question_text": question_text,
            "company": company,
            "role": role,
            "candidate_answer": payload.candidate_answer,
            "evaluation": evaluation.model_dump(),
            "created_at": datetime.now(timezone.utc)
        }
        r = await db.interview_sessions.insert_one(session_doc)
        session_doc["id"] = str(r.inserted_id)

        return {
            "session_id": str(r.inserted_id),
            "evaluation": evaluation.model_dump()
        }

    async def get_user_history(self, user_id: str, limit: int = 20) -> list[dict]:
        docs = await db.interview_sessions.find({"user_id": user_id}).sort("created_at", -1).limit(limit).to_list(limit)
        return [serialize(x) for x in docs]
