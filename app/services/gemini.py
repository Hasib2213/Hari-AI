from google import genai
from google.genai import types
from pydantic import BaseModel
from ..config import get_settings
from ..models.schemas import (
    IntentResult, MatchResult, ResumeAI, ResumeAnalysis, ATSAnalysis,
    CoverLetterAI, FieldMappingResponse
)

class GeminiService:
    def __init__(self):
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def structured(self, prompt: str, schema: type[BaseModel]):
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            ),
        )
        return schema.model_validate_json(response.text)

    async def intent(self, message: str):
        return await self.structured(f"""
You are a job-search/application agent router.
Classify the user's message into one allowed intent.
Never invent a job ID. Extract a concise search query when appropriate.
Allowed: more_jobs, search_jobs, adjust_preferences, company_question,
job_question, job_match_question, queue_job, start_applications,
resume_help, general.

MESSAGE:
{message}
""", IntentResult)

    async def match(self, profile, job):
        return await self.structured(f"""
Evaluate candidate fit for this job using ONLY supplied data.
Do not invent skills, experience, employers, education or authorization.
Score 0-100. Explain strongest fit factors and missing skills.

PROFILE:
{profile.model_dump_json()}

JOB:
{job.model_dump_json()}
""", MatchResult)

    async def resume(self, profile, job):
        return await self.structured(f"""
Create a truthful ATS-friendly job-specific resume.
Use only facts in the supplied candidate data. Never invent dates, employers,
metrics, certifications or skills. Emphasize relevant existing experience.

CANDIDATE:
{profile.model_dump_json()}

JOB:
{job.model_dump_json()}
""", ResumeAI)

    async def resume_analysis(self, resume_text: str):
        return await self.structured(f"""
Analyze this resume. Give a 0-100 score, letter grade, and concise fixes.
Separate urgent, critical and optional fixes. Do not invent facts.

RESUME:
{resume_text}
""", ResumeAnalysis)

    async def ats(self, resume_text: str, job):
        return await self.structured(f"""
Compare this resume with this job. Return ATS-style keyword and structure
analysis. Do not claim an exact vendor ATS score. Identify matched and missing
keywords and actionable recommendations.

RESUME:
{resume_text}

JOB:
{job.model_dump_json()}
""", ATSAnalysis)

    async def cover_letter(self, profile, job, instruction: str = ""):
        return await self.structured(f"""
Write a concise personalized cover letter for this job.
Use only truthful supplied candidate information. Never invent facts.
Additional user instruction: {instruction}

PROFILE:
{profile.model_dump_json()}

JOB:
{job.model_dump_json()}
""", CoverLetterAI)

    async def rewrite_cover_letter(self, letter: str, instruction: str):
        return await self.structured(f"""
Rewrite the supplied cover letter according to the instruction.
Preserve factual claims; do not invent experience.

LETTER:
{letter}

INSTRUCTION:
{instruction}
""", CoverLetterAI)

    async def map_fields(self, profile, resume_text: str, screening: dict, fields: list[dict]):
        return await self.structured(f"""
Map browser application fields to candidate data.
Only use supplied values. If a field is legal/authorization, demographic,
attestation, or otherwise requires a user decision and no explicit saved answer
exists, use user_required or skip. Never fabricate.
Return one mapping for each supplied field.

PROFILE:
{profile.model_dump_json()}

RESUME:
{resume_text}

SCREENING ANSWERS:
{screening}

FIELDS:
{fields}
""", FieldMappingResponse)

    async def answer(self, question: str, context: str):
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=f"""Answer using only the supplied context. If unknown, say so.
CONTEXT:
{context}
QUESTION:
{question}""",
            config=types.GenerateContentConfig(temperature=0.25),
        )
        return response.text or ""
