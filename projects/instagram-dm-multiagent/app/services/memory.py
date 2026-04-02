from app.core.config import get_settings
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.messages import MessageRepository
from app.db.repositories.kb import KnowledgeBaseRepository


class MemoryService:
    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
        knowledge_base: KnowledgeBaseRepository,
    ) -> None:
        self.settings = get_settings()
        self.conversations = conversations
        self.messages = messages
        self.knowledge_base = knowledge_base

    async def get_recent_history(self, thread_id: int, limit: int | None = None) -> list[dict[str, str]]:
        records = await self.messages.list_by_thread(thread_id, limit=limit or self.settings.default_history_limit)
        return [{"direction": message.direction, "text": message.text} for message in records]

    async def search_kb(self, query: str, language: str) -> list[dict[str, str]]:
        entries = await self.knowledge_base.search(query=query, language=language)
        return [
            {"question": entry.question, "answer": entry.answer, "category": entry.category, "tags": entry.tags}
            for entry in entries
        ]
