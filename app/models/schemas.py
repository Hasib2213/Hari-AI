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
