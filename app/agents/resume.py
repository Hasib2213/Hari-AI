import io
import pypdf
from ..services.gemini import GeminiService
from ..models.schemas import ParsedResumeProfile

def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text.strip()
    except Exception:
        return ""

class ResumeAgent:
    def __init__(self, ai: GeminiService | None = None):
        self.ai = ai or GeminiService()

    async def parse_file(self, file_bytes: bytes, filename: str = "", content_type: str = "application/pdf") -> ParsedResumeProfile:
        raw_text = ""
        is_pdf = filename.lower().endswith(".pdf") or "pdf" in content_type.lower()
        if is_pdf:
            raw_text = extract_pdf_text(file_bytes)
            try:
                parsed = await self.ai.parse_resume_multimodal(file_bytes, mime_type="application/pdf")
                if not parsed.raw_text and raw_text:
                    parsed.raw_text = raw_text
                return parsed
            except Exception:
                if raw_text:
                    parsed = await self.ai.parse_resume_text(raw_text)
                    parsed.raw_text = raw_text
                    return parsed
                raise
        else:
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            parsed = await self.ai.parse_resume_text(raw_text)
            parsed.raw_text = raw_text
            return parsed

    async def custom(self, profile, job):
        return await self.ai.resume(profile, job)

    async def analyze(self, text: str):
        return await self.ai.resume_analysis(text)

    async def ats(self, text: str, job):
        return await self.ai.ats(text, job)

    async def cover(self, profile, job, instruction: str = ""):
        return await self.ai.cover_letter(profile, job, instruction)

    async def optimize_section(self, company: str, title: str, bullets: list[str], raw_description: str = "", target_role: str = ""):
        return await self.ai.optimize_section(company, title, bullets, raw_description, target_role)
