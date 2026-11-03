import pytest
from types import SimpleNamespace
from app.services.matching import baseline
from app.models.schemas import UserProfile
from app.agents.matching import MatchingAgent

def test_matching():
    p = SimpleNamespace(skills=["python", "fastapi"], target_titles=["Software Engineer"], remote_only=True, preferred_locations=["Canada"], excluded_companies=[], employment_types=["full-time"])
    j = SimpleNamespace(skills=["python", "fastapi", "docker"], title="Software Engineer", remote=True, location="Canada", employment_type="full-time", company="Acme")
    score, overlap, missing = baseline(p, j)
    assert score > 50
    assert "python" in overlap
    assert "docker" in missing

@pytest.mark.anyio
async def test_fast_hybrid_ranking():
    profile = UserProfile(
        name="Test User",
        email="test@example.com",
        skills=["python", "fastapi", "docker"],
        target_titles=["Backend Engineer", "Software Engineer"],
        remote_only=True
    )
    raw_jobs = [
        {"title": "Backend Engineer", "company": "Company A", "location": "Remote", "remote": True, "skills": ["python", "fastapi"], "employment_type": "full-time"},
        {"title": "Junior Graphic Designer", "company": "Company B", "location": "New York", "remote": False, "skills": ["photoshop"], "employment_type": "full-time"},
        {"title": "Senior Python Architect", "company": "Company C", "location": "Remote", "remote": True, "skills": ["python", "docker", "fastapi"], "employment_type": "full-time"}
    ]
    # Pass None for AI to test the ultra-fast instant baseline & reasonings logic
    agent = MatchingAgent(ai=None)
    ranked = await agent.rank_and_explain(profile, raw_jobs, top_ai_count=0)

    assert len(ranked) == 3
    # Top job should be either Company C or Company A due to skill & title match
    assert ranked[0]["job"]["company"] in {"Company A", "Company C"}
    assert ranked[0]["match"]["score"] > ranked[-1]["match"]["score"]
    assert "photoshop" in ranked[-1]["match"]["missing_skills"]
