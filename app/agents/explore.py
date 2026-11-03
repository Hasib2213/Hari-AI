from datetime import datetime, timezone
from ..services.gemini import GeminiService
from ..repositories import jobs as job_repo, users as user_repo
from ..db import db
from ..utils.serialize import serialize
from ..models.schemas import CopilotChatResponse

def now():
    return datetime.now(timezone.utc)

class ExploreAgent:
    def __init__(self, ai: GeminiService | None = None):
        self.ai = ai or GeminiService()

    async def handle_chat(self, user_id: str, message: str) -> CopilotChatResponse:
        raw_user = await user_repo.get(user_id)
        user_profile = {k: v for k, v in raw_user.items() if k != "_id"} if raw_user else {}

        # Fetch recent chat history in chronological order
        recent_cursor = db.conversations.find({"user_id": user_id}).sort("created_at", -1).limit(10)
        recent_list = await recent_cursor.to_list(10)
        recent_list.reverse()

        history = []
        for doc in recent_list:
            role = doc.get("role") or ("user" if "message" in doc else "assistant")
            content = doc.get("content") or doc.get("message") or ""
            if content:
                history.append({"role": role, "content": content})

        # Ask Orion Copilot via Gemini
        copilot_turn = await self.ai.copilot_chat(user_profile, history, message)

        # Execute actions based on intent
        matched_jobs = []
        if copilot_turn.intent.intent in {"search_jobs", "more_jobs"}:
            query = copilot_turn.intent.search_query or message
            job_docs = await job_repo.search(query, 10)
            matched_jobs = [serialize(j) for j in job_docs]

        # Save User message
        await db.conversations.insert_one({
            "user_id": user_id,
            "role": "user",
            "content": message,
            "created_at": now()
        })

        # Save Assistant message
        await db.conversations.insert_one({
            "user_id": user_id,
            "role": "assistant",
            "content": copilot_turn.assistant_message,
            "intent": copilot_turn.intent.model_dump(),
            "created_at": now()
        })

        return CopilotChatResponse(
            assistant_message=copilot_turn.assistant_message,
            intent=copilot_turn.intent,
            jobs=matched_jobs,
            suggested_followups=copilot_turn.suggested_followups
        )

    # Legacy support
    async def handle(self, message: str):
        intent = await self.ai.intent(message)
        query = intent.search_query or message
        docs = await job_repo.search(query, 20)
        return intent, docs
