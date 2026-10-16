from ..services.gemini import GeminiService

class ResumeAgent:
    def __init__(self, ai): self.ai=ai

    async def custom(self, profile, job):
        return await self.ai.resume(profile,job)

    async def analyze(self, text):
        return await self.ai.resume_analysis(text)

    async def ats(self, text, job):
        return await self.ai.ats(text,job)

    async def cover(self, profile, job, instruction=""):
        return await self.ai.cover_letter(profile,job,instruction)
