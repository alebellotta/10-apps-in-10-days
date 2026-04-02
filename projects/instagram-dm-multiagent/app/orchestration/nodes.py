from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.classifier import IntentClassifierAgent
from app.agents.critic import CriticAgent
from app.agents.dispatch import DispatchAgent
from app.agents.drafter import ResponseDraftingAgent
from app.agents.escalation import EscalationAgent
from app.agents.policy import PolicyAgent
from app.agents.retriever import ContextRetrievalAgent
from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import ConversationState
from app.db.repositories.audit import AuditLogRepository
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.escalations import EscalationRepository
from app.db.repositories.kb import KnowledgeBaseRepository
from app.db.repositories.messages import MessageRepository
from app.domain.schemas.agent import DraftOutput
from app.orchestration.state import GraphState
from app.integrations.meta.client import MetaClient
from app.services.instagram import InstagramService
from app.services.llm import get_llm_adapter
from app.services.memory import MemoryService


logger = get_logger(__name__)


class NodeFactory:
    def __init__(self, session: AsyncSession) -> None:
        conversations = ConversationRepository(session)
        messages = MessageRepository(session)
        knowledge_base = KnowledgeBaseRepository(session)
        audit_logs = AuditLogRepository(session)
        llm = get_llm_adapter()
        memory = MemoryService(conversations=conversations, messages=messages, knowledge_base=knowledge_base)
        instagram = InstagramService(meta_client=MetaClient(), conversations=conversations, messages=messages)

        self.conversations = conversations
        self.messages = messages
        self.audit_logs = audit_logs
        self.escalations = EscalationRepository(session)
        self.classifier = IntentClassifierAgent(llm)
        self.retriever = ContextRetrievalAgent(llm, memory)
        self.policy = PolicyAgent(llm)
        self.drafter = ResponseDraftingAgent(llm)
        self.critic = CriticAgent(llm)
        self.escalation = EscalationAgent(llm)
        self.dispatch = DispatchAgent(instagram_service=instagram, audit_logs=audit_logs)
        self.session = session

    async def load_context_node(self, state: GraphState) -> GraphState:
        started = perf_counter()
        history = await MemoryService(self.conversations, self.messages, KnowledgeBaseRepository(self.session)).get_recent_history(state["thread_id"])
        state["conversation_history"] = history
        await self.audit_logs.create(
            thread_id=state["thread_id"],
            message_id=state["incoming_message_id"],
            action="load_context",
            actor_type="agent",
            actor_name="load_context",
            payload_json={"history_count": len(history)},
        )
        logger.info("graph_node_completed", node="load_context", duration_ms=(perf_counter() - started) * 1000)
        return state

    async def classifier_node(self, state: GraphState) -> GraphState:
        started = perf_counter()
        output = await self.classifier.run(
            text=state["incoming_text"],
            history=state.get("conversation_history", []),
            user_metadata={},
        )
        state["classifier_output"] = output
        logger.info("graph_node_completed", node="classifier", duration_ms=(perf_counter() - started) * 1000, intent=output.intent)
        return state

    async def retrieval_node(self, state: GraphState) -> GraphState:
        started = perf_counter()
        output = await self.retriever.run(
            thread_id=state["thread_id"],
            text=state["incoming_text"],
            intent=state["classifier_output"].intent,
            language=state["classifier_output"].language,
            history=state.get("conversation_history", []),
        )
        state["retrieval_output"] = output
        logger.info("graph_node_completed", node="retrieval", duration_ms=(perf_counter() - started) * 1000)
        return state

    async def policy_node(self, state: GraphState) -> GraphState:
        output = await self.policy.run(
            text=state["incoming_text"],
            classifier_output=state["classifier_output"],
            retrieval_output=state["retrieval_output"],
        )
        state["policy_output"] = output
        return state

    async def draft_node(self, state: GraphState) -> GraphState:
        output = await self.drafter.run(
            text=state["incoming_text"],
            classifier_output=state["classifier_output"],
            retrieval_output=state["retrieval_output"],
            constraints=state["policy_output"].safe_response_constraints,
        )
        state["draft_output"] = output
        return state

    async def critic_node(self, state: GraphState) -> GraphState:
        output = await self.critic.run(
            text=state["incoming_text"],
            draft_output=state["draft_output"],
            policy_output=state["policy_output"],
        )
        state["qa_output"] = output
        if output.final_decision == "revise":
            state["retry_count"] = state.get("retry_count", 0) + 1
            revised = output.revised_response or state["draft_output"].draft_response
            state["draft_output"] = DraftOutput(
                draft_response=revised,
                response_style=state["draft_output"].response_style,
                used_sources=state["draft_output"].used_sources,
                open_questions=state["draft_output"].open_questions,
            )
        return state

    async def escalation_node(self, state: GraphState) -> GraphState:
        output = await self.escalation.run(
            text=state["incoming_text"],
            classifier_output=state["classifier_output"],
            policy_output=state["policy_output"],
            draft_output=state.get("draft_output"),
        )
        state["escalation_output"] = output
        state["final_status"] = "escalated"
        await self.escalations.create(
            thread_id=state["thread_id"],
            message_id=state["incoming_message_id"],
            reason=output.escalation_reason,
            priority=output.priority,
            operator_summary=output.operator_summary,
            suggested_reply=output.suggested_reply,
        )
        return state

    async def dispatch_node(self, state: GraphState) -> GraphState:
        result = await self.dispatch.run(
            thread_id=state["thread_id"],
            recipient_id=state["recipient_id"],
            text=state["qa_output"].revised_response or state["draft_output"].draft_response,
        )
        state["dispatch_result"] = result
        state["final_status"] = "auto_replied"
        return state

    async def persist_node(self, state: GraphState) -> GraphState:
        conversation = await self.conversations.get_thread(state["thread_id"])
        if conversation is None or conversation.conversation_state is None:
            return state
        conversation.thread_status = state.get("final_status", "processed")
        conversation_state: ConversationState = conversation.conversation_state
        conversation_state.state_json = {
            "final_status": state.get("final_status"),
            "dispatch_result": state.get("dispatch_result"),
            "draft_output": state.get("draft_output").model_dump() if state.get("draft_output") else None,
            "escalation_output": state.get("escalation_output").model_dump() if state.get("escalation_output") else None,
        }
        conversation_state.last_classifier_output_json = (
            state.get("classifier_output").model_dump() if state.get("classifier_output") else None
        )
        conversation_state.last_policy_output_json = state.get("policy_output").model_dump() if state.get("policy_output") else None
        conversation_state.last_qa_output_json = state.get("qa_output").model_dump() if state.get("qa_output") else None
        await self.audit_logs.create(
            thread_id=state["thread_id"],
            message_id=state["incoming_message_id"],
            action="persist_state",
            actor_type="system",
            actor_name="graph",
            payload_json={"final_status": state.get("final_status")},
        )
        await self.session.flush()
        return state


def policy_router(state: GraphState) -> str:
    policy_output = state["policy_output"]
    if policy_output.risk_level == "high" or policy_output.requires_human_approval or not policy_output.allowed_to_auto_reply:
        return "escalation_node"
    return "draft_node"


def critic_router(state: GraphState) -> str:
    qa_output = state["qa_output"]
    if qa_output.final_decision == "send" and qa_output.approved:
        return "dispatch_node"
    if qa_output.final_decision == "revise" and state.get("retry_count", 0) <= get_settings().retry_draft_limit:
        return "draft_node"
    return "escalation_node"
