import pytest
from app.models.schemas import (
    InterviewQuestion, InterviewQuestionList, QuestionGuide,
    STAREvaluationResponse, STARComponentScore, InterviewPracticeRequest
)

def test_interview_schemas():
    q = InterviewQuestion(
        company="Amazon",
        role="Software Development Engineer",
        category="behavioral",
        difficulty="hard",
        question="Tell me about a time you had to make a decision with incomplete information.",
        tags=["Customer Obsession", "Bias for Action"]
    )
    assert q.company == "Amazon"
    assert q.category == "behavioral"
    assert len(q.tags) == 2

    q_list = InterviewQuestionList(questions=[q])
    assert len(q_list.questions) == 1

def test_star_evaluation_schema():
    eval_resp = STAREvaluationResponse(
        overall_score=85,
        situation=STARComponentScore(score=90, feedback="Clear context and business stakes."),
        task=STARComponentScore(score=80, feedback="Good delineation of personal ownership."),
        action=STARComponentScore(score=85, feedback="High agency actions detailed with technical depth."),
        result=STARComponentScore(score=85, feedback="Quantified metrics and business outcome stated."),
        strengths=["Strong ownership", "Quantifiable impact"],
        areas_for_improvement=["Could explain alternative approaches considered"],
        recommended_rewrite="At my previous role, I faced a critical latency spike..."
    )
    assert eval_resp.overall_score == 85
    assert eval_resp.situation.score == 90
    assert len(eval_resp.strengths) == 2
