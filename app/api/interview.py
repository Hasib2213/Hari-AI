from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from ..agents.interview import InterviewAgent
from ..services.gemini import GeminiService
from ..models.schemas import InterviewPracticeRequest

router = APIRouter(prefix="/api/interview", tags=["interview"])

def get_agent():
    return InterviewAgent(GeminiService())

@router.get("/questions")
async def list_questions(
    company: str = Query("Google", description="Company name like Google, Amazon, Meta, or all"),
    role: str = Query("Software Engineer", description="Role name like Software Engineer, Frontend, Product Manager"),
    category: str = Query("behavioral", description="behavioral, technical, system_design, situational, leadership"),
    limit: int = Query(10, ge=1, le=50)
):
    agent = get_agent()
    return await agent.get_questions(company=company, role=role, category=category, limit=limit)

@router.get("/questions/{question_id}/guide")
async def question_guide(question_id: str):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(400, "Invalid question id")
    agent = get_agent()
    try:
        return await agent.get_guide(question_id=question_id)
    except Exception as e:
        raise HTTPException(500, f"Error generating question guide: {str(e)}")

@router.post("/guide")
async def custom_question_guide(
    question_text: str = Query(..., description="The interview question text"),
    company: str = Query("General", description="Company name"),
    role: str = Query("Software Engineer", description="Role target")
):
    agent = get_agent()
    try:
        return await agent.get_guide(question_text=question_text, company=company, role=role)
    except Exception as e:
        raise HTTPException(500, f"Error generating guide: {str(e)}")

@router.post("/practice/evaluate")
async def evaluate_practice(payload: InterviewPracticeRequest):
    if not payload.candidate_answer.strip():
        raise HTTPException(400, "candidate_answer cannot be empty")
    agent = get_agent()
    try:
        return await agent.evaluate_practice(payload)
    except Exception as e:
        raise HTTPException(500, f"Evaluation error: {str(e)}")

@router.get("/history/{user_id}")
async def practice_history(user_id: str, limit: int = Query(20, ge=1, le=50)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user id")
    agent = get_agent()
    return await agent.get_user_history(user_id=user_id, limit=limit)
