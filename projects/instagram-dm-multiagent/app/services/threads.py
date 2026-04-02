from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.audit import AuditLogRepository
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.escalations import EscalationRepository
from app.db.repositories.messages import MessageRepository
from app.services.instagram import InstagramService
from app.integrations.meta.client import MetaClient


class ThreadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)
        self.escalations = EscalationRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.instagram = InstagramService(MetaClient(), self.conversations, self.messages)

    async def get_thread_detail(self, thread_id: int) -> dict:
        thread = await self.conversations.get_thread(thread_id)
        if thread is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
        latest_escalation = await self.escalations.get_latest_for_thread(thread_id)
        draft = None
        mode = thread.instagram_account.auto_reply_mode if thread.instagram_account else "assisted"
        if thread.conversation_state and thread.conversation_state.state_json:
            draft = thread.conversation_state.state_json.get("draft_output", {}) or {}
            draft = draft.get("draft_response")
        return {
            "thread": thread,
            "messages": thread.messages,
            "escalation": latest_escalation,
            "draft": draft,
            "mode": mode,
            "state": thread.conversation_state.state_json if thread.conversation_state else {},
        }

    async def approve_draft(self, thread_id: int, text: str | None = None) -> dict:
        detail = await self.get_thread_detail(thread_id)
        draft = text or detail["draft"]
        if not draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No draft available")
        inbound = next((message for message in reversed(detail["messages"]) if message.direction == "inbound"), None)
        if inbound is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inbound message available")
        message, result = await self.instagram.send_reply(thread_id=thread_id, recipient_id=inbound.sender_id, text=draft)
        escalation = detail["escalation"]
        if escalation and escalation.status == "pending":
            await self.escalations.resolve(escalation)
        await self.audit_logs.create(
            thread_id=thread_id,
            message_id=message.id,
            action="human_approved_draft",
            actor_type="human",
            actor_name="dashboard",
            payload_json=result,
        )
        return {"status": "sent", "message_id": message.id}

    async def send_manual_message(self, thread_id: int, text: str) -> dict:
        detail = await self.get_thread_detail(thread_id)
        inbound = next((message for message in reversed(detail["messages"]) if message.direction == "inbound"), None)
        if inbound is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No inbound message available")
        message, result = await self.instagram.send_reply(thread_id=thread_id, recipient_id=inbound.sender_id, text=text)
        await self.audit_logs.create(
            thread_id=thread_id,
            message_id=message.id,
            action="human_manual_send",
            actor_type="human",
            actor_name="dashboard",
            payload_json=result,
        )
        return {"status": "sent", "message_id": message.id}
