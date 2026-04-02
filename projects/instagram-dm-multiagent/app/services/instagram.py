from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.messages import MessageRepository
from app.integrations.meta.client import MetaClient
from app.integrations.meta.schemas import NormalizedInstagramEvent


class InstagramService:
    def __init__(
        self,
        meta_client: MetaClient,
        conversations: ConversationRepository,
        messages: MessageRepository,
    ) -> None:
        self.meta_client = meta_client
        self.conversations = conversations
        self.messages = messages

    async def ingest_message(self, event: NormalizedInstagramEvent):
        conversation = await self.conversations.get_or_create_by_external_ids(
            thread_external_id=event.thread_external_id,
            user_external_id=event.sender_id,
        )
        existing = await self.messages.get_by_external_id(event.message_external_id)
        if existing:
            return conversation, existing
        message = await self.messages.create(
            thread_id=conversation.id,
            external_message_id=event.message_external_id,
            direction="inbound",
            sender_id=event.sender_id,
            recipient_id=event.recipient_id,
            text=event.text,
            raw_payload_json=event.raw_payload,
        )
        await self.conversations.touch_thread(conversation.id)
        return conversation, message

    async def send_reply(self, thread_id: int, recipient_id: str, text: str):
        result = await self.meta_client.send_dm_reply(recipient_id=recipient_id, text=text)
        message = await self.messages.create(
            thread_id=thread_id,
            external_message_id=result.get("message_id", f"outbound-{thread_id}-{abs(hash(text))}"),
            direction="outbound",
            sender_id="brand",
            recipient_id=recipient_id,
            text=text,
            raw_payload_json=result,
            delivery_status="sent",
        )
        await self.conversations.touch_thread(thread_id)
        return message, result
