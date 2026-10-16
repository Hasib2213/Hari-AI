from ..services.gemini import GeminiService
from ..repositories import jobs as job_repo

class ExploreAgent:
    def __init__(self, ai: GeminiService):
        self.ai=ai

    async def handle(self, message: str):
        intent=await self.ai.intent(message)
        query=intent.search_query or message
        docs=await job_repo.search(query,20)
        return intent, docs
