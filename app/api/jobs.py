from fastapi import APIRouter, HTTPException
from ..models.schemas import JobCreate
from ..repositories import jobs
from ..utils.serialize import serialize
from datetime import datetime, timezone

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

SAMPLE_TECH_JOBS = [
    {
        "title": "Senior AI & Machine Learning Engineer",
        "company": "OpenAI",
        "description": "Build high-throughput LLM workflows, fine-tune models, and architect scalable AI agent platforms. Experience with Python, PyTorch, FastAPI, and vector databases required.",
        "location": "San Francisco, CA",
        "employment_type": "full-time",
        "remote": True,
        "level": "senior",
        "salary_min": 190000,
        "salary_max": 260000,
        "url": "https://openai.com/careers/ai-engineer",
        "source": "seed",
        "skills": ["python", "fastapi", "gemini", "pytorch", "docker", "llm", "mongodb"],
        "category": "ai_ml"
    },
    {
        "title": "Senior Software Engineer (Backend & Cloud)",
        "company": "Google",
        "description": "Design and build resilient, distributed cloud services. Solid understanding of concurrency, APIs, and microservices in Python, Go, or Java.",
        "location": "Toronto, Canada",
        "employment_type": "full-time",
        "remote": False,
        "level": "senior",
        "salary_min": 160000,
        "salary_max": 230000,
        "url": "https://careers.google.com/jobs/results/123",
        "source": "seed",
        "skills": ["python", "go", "fastapi", "cloud", "docker", "kubernetes", "sql"],
        "category": "backend"
    },
    {
        "title": "Software Development Engineer II (SDE II)",
        "company": "Amazon",
        "description": "Own core AWS and e-commerce services supporting millions of requests per second. Requires deep knowledge of distributed systems and high-availability architecture.",
        "location": "Seattle, WA",
        "employment_type": "full-time",
        "remote": True,
        "level": "mid",
        "salary_min": 145000,
        "salary_max": 200000,
        "url": "https://amazon.jobs/en/jobs/456",
        "source": "seed",
        "skills": ["python", "java", "aws", "docker", "microservices", "sql"],
        "category": "backend"
    },
    {
        "title": "Senior Full Stack Engineer (React & TypeScript)",
        "company": "Shopify",
        "description": "Build merchant-facing experiences with modern React, TypeScript, GraphQL, and scalable backend services. Digital by default (100% remote).",
        "location": "Remote, Canada",
        "employment_type": "full-time",
        "remote": True,
        "level": "senior",
        "salary_min": 150000,
        "salary_max": 210000,
        "url": "https://shopify.com/careers/789",
        "source": "seed",
        "skills": ["react", "typescript", "javascript", "graphql", "next.js", "node.js"],
        "category": "fullstack"
    },
    {
        "title": "Frontend Software Engineer",
        "company": "Stripe",
        "description": "Craft intuitive financial dashboards and payment checkout experiences. Deep proficiency in modern web architecture, state management, and performance.",
        "location": "Remote, US",
        "employment_type": "full-time",
        "remote": True,
        "level": "mid",
        "salary_min": 140000,
        "salary_max": 195000,
        "url": "https://stripe.com/jobs/321",
        "source": "seed",
        "skills": ["react", "typescript", "javascript", "css", "html", "rest"],
        "category": "frontend"
    },
    {
        "title": "AI Agent & Infrastructure Engineer",
        "company": "Meta",
        "description": "Build agentic automation frameworks, Playwright-based integrations, and automated pipelines connecting large language models to external tools.",
        "location": "Menlo Park, CA",
        "employment_type": "full-time",
        "remote": True,
        "level": "senior",
        "salary_min": 185000,
        "salary_max": 255000,
        "url": "https://metacareers.com/jobs/654",
        "source": "seed",
        "skills": ["python", "playwright", "fastapi", "llm", "docker", "mongodb"],
        "category": "ai_ml"
    }
]

@router.post("")
async def ingest(payload: JobCreate):
    d = payload.model_dump()
    d["created_at"] = datetime.now(timezone.utc)
    return serialize(await jobs.create(d))

@router.post("/seed")
async def seed_jobs():
    """Seed sample realistic tech jobs for immediate Jobright-style matching test."""
    seeded = []
    for item in SAMPLE_TECH_JOBS:
        item["created_at"] = datetime.now(timezone.utc)
        saved = await jobs.create(item)
        seeded.append(serialize(saved))
    return {"message": f"Successfully seeded {len(seeded)} jobs", "jobs": seeded}

@router.get("")
async def list_jobs(query: str = "", limit: int = 20):
    return [serialize(x) for x in await jobs.search(query, min(limit, 50))]

@router.get("/{job_id}")
async def get(job_id: str):
    d = await jobs.get(job_id)
    if not d:
        raise HTTPException(404, "Job not found")
    return serialize(d)
