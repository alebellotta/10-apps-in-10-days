import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agents.classifier import IntentClassifierAgent
from app.agents.policy import PolicyAgent
from app.agents.critic import CriticAgent
from app.db.base import Base
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.kb import KnowledgeBaseRepository
from app.db.repositories.messages import MessageRepository
from app.domain.schemas.agent import DraftOutput, PolicyOutput
from app.services.llm import MockLLMAdapter


@pytest.mark.asyncio
async def test_classifier_output_parsing():
    agent = IntentClassifierAgent(MockLLMAdapter())
    result = await agent.run("Vorrei conoscere i prezzi", [], {})
    assert result.intent in {"lead", "faq"}
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_policy_routes_sensitive_messages():
    classifier = await IntentClassifierAgent(MockLLMAdapter()).run("Ho bisogno di un rimborso", [], {})
    retrieval = await MockLLMAdapter().generate_structured("retrieval", __import__("app.domain.schemas.agent", fromlist=["RetrievalOutput"]).RetrievalOutput)
    result = await PolicyAgent(MockLLMAdapter()).run("Ho bisogno di un rimborso", classifier, retrieval)
    assert result.requires_human_approval is True
    assert result.allowed_to_auto_reply is False


@pytest.mark.asyncio
async def test_critic_escalates_sensitive_draft():
    critic = CriticAgent(MockLLMAdapter())
    draft = DraftOutput(
        draft_response="Ti aiuto subito con il rimborso.",
        response_style="friendly_professional",
        used_sources=[],
        open_questions=[],
    )
    policy = PolicyOutput(
        allowed_to_auto_reply=False,
        risk_level="high",
        policy_flags=["refund_request"],
        requires_human_approval=True,
        safe_response_constraints=["Do not promise refunds"],
    )
    result = await critic.run("Voglio un rimborso", draft, policy)
    assert result.final_decision == "escalate"


@pytest.mark.asyncio
async def test_repository_basic_flow():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_maker() as session:
        conversations = ConversationRepository(session)
        messages = MessageRepository(session)
        kb = KnowledgeBaseRepository(session)
        thread = await conversations.get_or_create_by_external_ids("thread-1", "user-1")
        await messages.create(thread.id, "mid-1", "inbound", "user-1", "brand", "ciao", {})
        await kb.create(category="faq", question="Orari?", answer="9-18", language="it", tags="orari")
        await session.commit()

        history = await messages.list_by_thread(thread.id)
        results = await kb.search("orari", "it")
        assert len(history) == 1
        assert len(results) == 1
    await engine.dispose()
