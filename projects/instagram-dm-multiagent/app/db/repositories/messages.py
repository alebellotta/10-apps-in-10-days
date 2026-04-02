from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        thread_id: int,
        external_message_id: str,
        direction: str,
        sender_id: str,
        recipient_id: str,
        text: str,
        raw_payload_json: dict,
        delivery_status: str = "received",
    ) -> Message:
        message = Message(
            thread_id=thread_id,
            external_message_id=external_message_id,
            direction=direction,
            sender_id=sender_id,
            recipient_id=recipient_id,
            text=text,
            raw_payload_json=raw_payload_json,
            delivery_status=delivery_status,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_by_thread(self, thread_id: int, limit: int | None = None) -> list[Message]:
        stmt = select(Message).where(Message.thread_id == thread_id).order_by(desc(Message.message_timestamp))
        if limit:
            stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def get_by_external_id(self, external_message_id: str) -> Message | None:
        result = await self.session.execute(select(Message).where(Message.external_message_id == external_message_id))
        return result.scalar_one_or_none()

    async def get(self, message_id: int) -> Message | None:
        result = await self.session.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()
