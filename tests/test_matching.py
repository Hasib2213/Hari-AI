from types import SimpleNamespace
from app.services.matching import baseline
def test_matching():
    p=SimpleNamespace(skills=["python","fastapi"],target_titles=["Software Engineer"],remote_only=True,preferred_locations=["Canada"],excluded_companies=[],employment_types=["full-time"])
    j=SimpleNamespace(skills=["python","fastapi","docker"],title="Software Engineer",remote=True,location="Canada",employment_type="full-time",company="Acme")
    score,overlap,missing=baseline(p,j)
    assert score>50
    assert "python" in overlap
    assert "docker" in missing
