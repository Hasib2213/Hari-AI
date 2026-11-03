from google import genai
from google.genai import types
from pydantic import BaseModel
from ..config import get_settings
from ..models.schemas import (
    IntentResult, MatchResult, ResumeAI, ResumeAnalysis, ATSAnalysis,
    CoverLetterAI, FieldMappingResponse,
    InterviewQuestionList, QuestionGuide, STAREvaluationResponse,
    ParsedResumeProfile, CopilotTurnResult, OptimizedSectionResponse
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

    async def generate_company_questions(self, company: str, role: str, category: str = "behavioral", count: int = 5):
        return await self.structured(f"""
You are an expert FAANG and top-tier tech interview coach (identical to Jobright.ai).
Generate {count} realistic, actual interview questions commonly asked at {company} for a {role} position under the category '{category}'.
- If company is Amazon, emphasize Amazon Leadership Principles (Customer Obsession, Bias for Action, Deliver Results, etc.).
- If company is Google, emphasize Googleyness, ambiguity navigation, and general cognitive problem-solving.
- If company is Meta, emphasize fast execution, scaling, data-driven decisions, and systems architecture.
- If company is General or any other company, tailor to high-bar industry standards for {role}.
Include relevant tags and difficulty level (easy, medium, hard).

COMPANY: {company}
ROLE: {role}
CATEGORY: {category}
COUNT: {count}
""", InterviewQuestionList)

    async def get_question_guide(self, company: str, role: str, question: str):
        return await self.structured(f"""
You are an expert interview coach analyzing a real interview question for {company} (Role: {role}).
QUESTION:
{question}

Provide an in-depth breakdown:
1. Interviewer Intent: What psychological traits, technical signals, or behavioral competencies is the interviewer evaluating?
2. Key Points: Bullet points the candidate MUST include to score top marks.
3. Recommended Framework: Framework to structure the answer (e.g., STAR Method for behavioral, 4-step framework for system design).
4. Ideal Model Answer: A complete, natural, and persuasive senior-level example response.
5. Common Pitfalls: Frequent mistakes, red flags, and rambling traps candidates fall into.
""", QuestionGuide)

    async def evaluate_star_answer(self, question: str, company: str, role: str, candidate_answer: str, candidate_profile: dict | None = None):
        return await self.structured(f"""
You are an expert FAANG bar-raiser and interview evaluator using the STAR (Situation, Task, Action, Result) method.
Evaluate the candidate's answer to this question:

COMPANY: {company}
ROLE: {role}
QUESTION: {question}

CANDIDATE ANSWER:
{candidate_answer}

CANDIDATE CONTEXT:
{candidate_profile or 'None provided'}

Evaluation Criteria:
- Situation: Did they set up the business context, complexity, and stakes clearly without rambling? (Score 0-100 + feedback)
- Task: Did they clarify their personal ownership vs the team's role? (Score 0-100 + feedback)
- Action: Did they detail specific, high-agency actions, technical decisions, and personal initiatives using 'I' instead of 'we'? (Score 0-100 + feedback)
- Result: Did they present quantifiable business outcomes, metrics, or key technical learnings? (Score 0-100 + feedback)
- Overall Score: 0-100 composite grade.
- Strengths: What was done well.
- Areas for Improvement: Concrete actionable tips to elevate the answer.
- Recommended Rewrite: Provide a rewritten version of their story using the STAR framework. Retain all their truthful facts, but make it articulate, impactful, and memorable.
""", STAREvaluationResponse)

    async def parse_resume_multimodal(self, pdf_bytes: bytes, mime_type: str = "application/pdf"):
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type=mime_type),
                """
You are an expert resume parsing engine identical to Jobright.ai.
Extract candidate contact info, target titles, summary, skills, years of experience, education, and individual work experiences with bullet points.
Never hallucinate or invent employers, dates, or skills.
"""
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ParsedResumeProfile,
                temperature=0.1,
            ),
        )
        return ParsedResumeProfile.model_validate_json(response.text)

    async def parse_resume_text(self, text: str):
        return await self.structured(f"""
You are an expert resume parsing engine identical to Jobright.ai.
Extract candidate contact info, target titles, summary, skills, years of experience, education, and individual work experiences with bullet points.
Never hallucinate or invent employers, dates, or skills.

RESUME CONTENT:
{text}
""", ParsedResumeProfile)

    async def copilot_chat(self, user_profile: dict, history: list[dict], message: str):
        hist_text = ""
        for h in history[-8:]:
            role = h.get("role", "user")
            content = h.get("content", "")
            hist_text += f"{role.upper()}: {content}\n"

        return await self.structured(f"""
You are 'Orion', the intelligent, friendly, and highly strategic AI career copilot (identical to Jobright.ai).
Your job is to assist the candidate with their job search, company research, resume feedback, interview prep, salary negotiation, and career strategy.

CANDIDATE CONTEXT:
Name: {user_profile.get('name', 'Candidate')}
Target Titles: {user_profile.get('target_titles', [])}
Skills: {user_profile.get('skills', [])}
Experience Years: {user_profile.get('years_experience', 0)}
Preferred Locations: {user_profile.get('preferred_locations', [])}
Remote Only: {user_profile.get('remote_only', False)}

RECENT CONVERSATION HISTORY:
{hist_text or "No prior history"}

NEW USER MESSAGE:
{message}

INSTRUCTIONS:
1. Classify the intent strictly into one of:
   - more_jobs, search_jobs, adjust_preferences, company_question,
     job_question, job_match_question, queue_job, start_applications,
     resume_help, general.
2. Formulate 'assistant_message': An empathetic, actionable, senior-level response maintaining multi-turn context.
3. Suggest 2-3 concise 'suggested_followups' (prompts the user can click next).
""", CopilotTurnResult)

    async def optimize_section(self, company: str, title: str, bullets: list[str], raw_description: str = "", target_role: str = ""):
        return await self.structured(f"""
You are the Jobright.ai Resume Section Optimizer (the 1-Click "FIX" Engine).
Optimize the work experience bullet points for this specific role and company.

COMPANY: {company}
JOB TITLE: {title}
TARGET ROLE: {target_role or title}
DESCRIPTION CONTEXT:
{raw_description}

EXISTING BULLET POINTS:
{bullets}

INSTRUCTIONS:
1. Identify any urgent issues (e.g. passive verbs like 'worked on', lack of quantifiable metrics or percentages, vague responsibilities).
2. Rewrite each bullet point strictly applying Google's XYZ formula:
   "Accomplished [X] as measured by [Y], by doing [Z]"
3. Start every optimized bullet with a strong action verb (e.g., Architected, Engineered, Optimized, Spearheaded, Accelerated, Streamlined).
4. Preserve all true technologies, tools, and factual domains mentioned (e.g., if Java, Spring Boot, Kafka, Docker are mentioned, retain and elevate them).
5. Add realistic, plausible quantifiable engineering metrics (e.g. latency reduced by X%, 99.9% uptime, 2M+ active users, 40% efficiency) appropriate for a senior professional at {company}.
6. Provide a breakdown for each bullet explaining the action verb used, the quantifiable metric introduced, and why the new version is significantly better for hiring managers and ATS.
""", OptimizedSectionResponse)
