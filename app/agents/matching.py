import asyncio
from ..services.gemini import GeminiService
from ..services.matching import baseline
from ..models.schemas import UserProfile, JobCreate, MatchResult
from ..utils.serialize import serialize

class MatchingAgent:
    def __init__(self, ai: GeminiService | None = None):
        self.ai = ai or GeminiService()

    async def score(self, profile: UserProfile, job: JobCreate) -> MatchResult:
        base, overlap, missing = baseline(profile, job)
        try:
            result = await self.ai.match(profile, job)
            return result
        except Exception:
            return MatchResult(
                score=base,
                reasons=[f"{len(overlap)} relevant skill(s) overlap"],
                matching_skills=overlap,
                missing_skills=missing
            )

    async def rank_and_explain(self, profile: UserProfile, raw_jobs: list[dict], top_ai_count: int = 5) -> list[dict]:
        scored_candidates = []
        for raw in raw_jobs:
            clean_job_dict = {k: v for k, v in raw.items() if k not in {"_id", "created_at", "fingerprint"}}
            j = JobCreate(**clean_job_dict)
            base_score, overlap, missing = baseline(profile, j)
            scored_candidates.append({
                "raw": raw,
                "job": j,
                "base_score": base_score,
                "overlap": overlap,
                "missing": missing
            })

        # Instantaneous baseline sort
        scored_candidates.sort(key=lambda x: x["base_score"], reverse=True)

        async def evaluate_item(item, use_ai=False):
            if use_ai:
                try:
                    m = await self.ai.match(profile, item["job"])
                    return {"job": serialize(item["raw"]), "match": m.model_dump()}
                except Exception:
                    pass

            reasons = []
            if item["overlap"]:
                reasons.append(f"Matching skills: {', '.join(item['overlap'][:4])}")
            if any(t.lower() in item["job"].title.lower() for t in profile.target_titles):
                reasons.append(f"Matches your target title: {item['job'].title}")
            if profile.remote_only and item["job"].remote:
                reasons.append("Matches your remote-only preference")
            if not reasons:
                reasons.append(f"{len(item['overlap'])} skill(s) matched")

            return {
                "job": serialize(item["raw"]),
                "match": {
                    "score": item["base_score"],
                    "reasons": reasons,
                    "matching_skills": item["overlap"],
                    "missing_skills": item["missing"]
                }
            }

        tasks = []
        for i, item in enumerate(scored_candidates):
            tasks.append(evaluate_item(item, use_ai=(i < top_ai_count)))

        results = await asyncio.gather(*tasks)
        results.sort(key=lambda x: x["match"]["score"], reverse=True)
        return results
