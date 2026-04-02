from app.agents.prompts.retriever_prompt import build_retrieval_prompt
from app.domain.schemas.agent import RetrievalOutput
from app.integrations.llm.base import LLMAdapter
from app.services.memory import MemoryService


class ContextRetrievalAgent:
    def __init__(self, llm: LLMAdapter, memory_service: MemoryService) -> None:
        self.llm = llm
        self.memory_service = memory_service

    async def run(self, thread_id: int, text: str, intent: str, language: str, history: list[dict[str, str]]) -> RetrievalOutput:
        kb_entries = await self.memory_service.search_kb(query=text, language=language)
        prompt = build_retrieval_prompt(text=text, intent=intent, history=history, kb_entries=kb_entries)
        output = await self.llm.generate_structured(prompt, RetrievalOutput)
        if kb_entries and not output.relevant_faq_entries:
            output.relevant_faq_entries = kb_entries
        return output
