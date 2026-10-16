from ..services.gemini import GeminiService
from ..services.matching import baseline
from ..models.schemas import UserProfile, JobCreate

class MatchingAgent:
    def __init__(self, ai): self.ai=ai

    async def score(self, profile, job):
        base, overlap, missing=baseline(profile,job)
        try:
            result=await self.ai.match(profile,job)
            return result
        except Exception:
            from ..models.schemas import MatchResult
            return MatchResult(score=base,
                reasons=[f"{len(overlap)} relevant skill(s) overlap"],
                matching_skills=overlap, missing_skills=missing)
