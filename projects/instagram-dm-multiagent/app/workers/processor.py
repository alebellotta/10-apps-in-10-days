import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.repositories.audit import AuditLogRepository
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.events import IncomingEventRepository
from app.db.repositories.messages import MessageRepository
from app.db.session import AsyncSessionLocal
from app.integrations.meta.schemas import NormalizedInstagramEvent
from app.services.instagram import InstagramService
from app.services.orchestration import OrchestrationService
from app.services.queue import QueueService
from app.integrations.meta.client import MetaClient


logger = get_logger(__name__)


class EventProcessor:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.events = IncomingEventRepository(session)
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.instagram = InstagramService(MetaClient(), self.conversations, self.messages)
        self.orchestration = OrchestrationService(session)

    async def process_event(self, event_id: int) -> None:
        event = await self.events.get(event_id)
        if event is None:
            return
        if event.processing_status == "processed":
            return
        try:
            normalized = NormalizedInstagramEvent.model_validate(event.payload_json)
            conversation, message = await self.instagram.ingest_message(normalized)
            await self.audit_logs.create(
                thread_id=conversation.id,
                message_id=message.id,
                action="event_ingested",
                actor_type="system",
                actor_name="webhook",
                payload_json={"event_id": event.id},
            )
            result = await self.orchestration.run(
                {
                    "event_id": event.id,
                    "thread_id": conversation.id,
                    "incoming_message_id": message.id,
                    "incoming_text": message.text,
                    "recipient_id": normalized.sender_id,
                    "errors": [],
                    "retry_count": 0,
                }
            )
            await self.events.mark_processed(event)
            logger.info("event_processed", event_id=event.id, final_status=result.get("final_status"))
            await self.session.commit()
        except Exception as exc:
            await self.events.mark_failed(event, str(exc))
            await self.session.commit()
            logger.exception("event_processing_failed", event_id=event_id)
            raise


class WorkerRuntime:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.queue = QueueService()
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if not self.settings.worker_enabled:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            await asyncio.wait_for(self._task, timeout=5)

    async def _loop(self) -> None:
        while self._running:
            event_id = await self.queue.dequeue_event()
            if event_id is None:
                continue
            async with AsyncSessionLocal() as session:
                processor = EventProcessor(session)
                try:
                    await processor.process_event(event_id)
                except Exception:
                    continue
