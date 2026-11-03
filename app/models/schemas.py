from typing import Literal, Any
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    target_titles: list[str] = []
    preferred_locations: list[str] = []
    remote_only: bool = False
    employment_types: list[str] = ["full-time"]
    seniority: list[str] = []
    salary_min: int | None = None
    excluded_companies: list[str] = []
    skills: list[str] = []
    years_experience: float = 0
    education: list[str] = []
    work_authorization: str | None = None
    screening_answers: dict[str, str] = {}
    resume_text: str = ""

class JobCreate(BaseModel):
    title: str
    company: str
    description: str = ""
    location: str = ""
    employment_type: str = "full-time"
    remote: bool = False
    level: str = "mid"
    salary_min: int | None = None
    salary_max: int | None = None
    url: str | None = None
    source: str = "manual"
    skills: list[str] = []
    category: str | None = None
    source_job_id: str | None = None

class IntentResult(BaseModel):
    intent: Literal[
        "more_jobs","search_jobs","adjust_preferences","company_question",
        "job_question","job_match_question","queue_job","start_applications",
        "resume_help","general"
    ]
    search_query: str = ""
    company: str = ""
    job_id: str = ""
    response: str = ""

class MatchResult(BaseModel):
    score: int = Field(ge=0, le=100)
    reasons: list[str] = []
    matching_skills: list[str] = []
    missing_skills: list[str] = []

class ResumeAI(BaseModel):
    title: str
    summary: str
    skills: list[str]
    experience_bullets: list[str]
    full_text: str

class ResumeAnalysis(BaseModel):
    grade: str
    score: int = Field(ge=0, le=100)
    urgent_fixes: list[str] = []
    critical_fixes: list[str] = []
    optional_fixes: list[str] = []

class ATSAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    structural_issues: list[str] = []
    recommendations: list[str] = []

class CoverLetterAI(BaseModel):
    letter: str

class FieldMapping(BaseModel):
    selector: str
    field_label: str
    value_source: Literal["profile","resume","screening_answer","skip","user_required"]
    value: str = ""
    confidence: float = Field(ge=0, le=1)
    reason: str = ""

class FieldMappingResponse(BaseModel):
    mappings: list[FieldMapping]

class ChatRequest(BaseModel):
    message: str

class ApplicationQueueItem(BaseModel):
    job_id: str
    status: Literal["queued","running","completed","failed","skipped"] = "queued"

class ApplicationRunResponse(BaseModel):
    id: str
    status: str
    current_step: str
    jobs_remaining: int
    queue: list[dict[str, Any]]

class InterviewQuestion(BaseModel):
    id: str | None = None
    company: str
    role: str
    category: Literal["behavioral", "technical", "system_design", "situational", "leadership"]
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    question: str
    tags: list[str] = []

class InterviewQuestionList(BaseModel):
    questions: list[InterviewQuestion]

class QuestionGuide(BaseModel):
    interviewer_intent: str
    key_points_to_cover: list[str]
    recommended_framework: str
    ideal_model_answer: str
    common_pitfalls: list[str]

class STARComponentScore(BaseModel):
    score: int = Field(ge=0, le=100)
    feedback: str

class STAREvaluationResponse(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    situation: STARComponentScore
    task: STARComponentScore
    action: STARComponentScore
    result: STARComponentScore
    strengths: list[str]
    areas_for_improvement: list[str]
    recommended_rewrite: str

class InterviewPracticeRequest(BaseModel):
    question_id: str | None = None
    question_text: str
    company: str = "General"
    role: str = "Software Engineer"
    candidate_answer: str
    user_id: str | None = None

class WorkExperienceItem(BaseModel):
    company: str
    title: str
    start_date: str = ""
    end_date: str = ""
    bullets: list[str] = []

class ParsedResumeProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str = ""
    target_titles: list[str] = []
    skills: list[str] = []
    years_experience: float = 0
    education: list[str] = []
    work_experience: list[WorkExperienceItem] = []
    raw_text: str = ""

class CopilotTurnResult(BaseModel):
    intent: IntentResult
    assistant_message: str
    suggested_followups: list[str] = []

class CopilotChatResponse(BaseModel):
    assistant_message: str
    intent: IntentResult
    jobs: list[dict[str, Any]] = []
    suggested_followups: list[str] = []

class ChatMessageRecord(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str | None = None

class BulletImprovement(BaseModel):
    original: str
    optimized: str
    action_verb: str
    quantifiable_metric: str
    why_better: str

class OptimizedSectionResponse(BaseModel):
    company: str
    title: str
    issues_fixed: list[str] = []
    optimized_bullets: list[str]
    bullet_breakdowns: list[BulletImprovement] = []

class OptimizeSectionRequest(BaseModel):
    company: str
    title: str
    bullets: list[str] = []
    raw_description: str | None = ""
    target_role: str | None = ""
    user_id: str | None = None
