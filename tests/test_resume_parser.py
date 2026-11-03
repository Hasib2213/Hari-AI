import pytest
from app.models.schemas import ParsedResumeProfile, WorkExperienceItem, CopilotChatResponse, IntentResult

def test_parsed_resume_profile():
    parsed = ParsedResumeProfile(
        name="Hasibul Hasan",
        email="hasib@example.com",
        phone="+1234567890",
        location="Toronto, Canada",
        linkedin_url="https://linkedin.com/in/hasib",
        github_url="https://github.com/hasib",
        summary="Senior AI & Backend Engineer with 5 years experience.",
        target_titles=["AI Engineer", "Backend Engineer"],
        skills=["Python", "FastAPI", "Gemini", "MongoDB"],
        years_experience=5.0,
        education=["B.Sc. in Computer Science"],
        work_experience=[
            WorkExperienceItem(
                company="Tech Corp",
                title="AI Engineer",
                start_date="2022",
                end_date="Present",
                bullets=["Built LLM agent workflows", "Optimized latency by 35%"]
            )
        ],
        raw_text="Full resume text..."
    )
    assert parsed.name == "Hasibul Hasan"
    assert "FastAPI" in parsed.skills
    assert len(parsed.work_experience) == 1
    assert parsed.work_experience[0].company == "Tech Corp"

def test_copilot_response_schema():
    copilot_res = CopilotChatResponse(
        assistant_message="Hello! I found 3 great senior AI jobs matching your Python and Gemini experience.",
        intent=IntentResult(intent="search_jobs", search_query="senior AI engineer"),
        jobs=[{"title": "Senior AI Engineer", "company": "Acme AI"}],
        suggested_followups=["Tailor my resume for Acme AI", "What are the required skills?"]
    )
    assert copilot_res.intent.intent == "search_jobs"
    assert len(copilot_res.jobs) == 1
    assert len(copilot_res.suggested_followups) == 2

def test_optimize_section_schema():
    from app.models.schemas import OptimizedSectionResponse, BulletImprovement, OptimizeSectionRequest
    req = OptimizeSectionRequest(
        company="Citibank, N.A.",
        title="Senior Java Developer",
        bullets=["Worked on core banking microservices with Spring Boot."],
        raw_description="Developed secure APIs for credit cards."
    )
    assert req.company == "Citibank, N.A."
    assert len(req.bullets) == 1

    resp = OptimizedSectionResponse(
        company="Citibank, N.A.",
        title="Senior Java Developer",
        issues_fixed=["Replaced passive verb with high-impact action verb", "Added quantifiable scale metrics"],
        optimized_bullets=[
            "Architected Spring Boot microservices processing 2M+ daily credit-card transactions with 99.99% uptime."
        ],
        bullet_breakdowns=[
            BulletImprovement(
                original="Worked on core banking microservices with Spring Boot.",
                optimized="Architected Spring Boot microservices processing 2M+ daily credit-card transactions with 99.99% uptime.",
                action_verb="Architected",
                quantifiable_metric="2M+ daily transactions, 99.99% uptime",
                why_better="Uses Google XYZ formula and quantifiable business impact."
            )
        ]
    )
    assert len(resp.optimized_bullets) == 1
    assert len(resp.bullet_breakdowns) == 1
    assert resp.bullet_breakdowns[0].action_verb == "Architected"
