from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IncomingEvent


class IncomingEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, external_event_id: str, event_type: str, payload_json: dict[str, Any]) -> IncomingEvent:
        existing = await self.get_by_external_id(external_event_id)
        if existing:
            return existing
        event = IncomingEvent(
            external_event_id=external_event_id,
            event_type=event_type,
            payload_json=payload_json,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get(self, event_id: int) -> IncomingEvent | None:
        result = await self.session.execute(select(IncomingEvent).where(IncomingEvent.id == event_id))
        return result.scalar_one_or_none()

    async def get_by_external_id(self, external_event_id: str) -> IncomingEvent | None:
        result = await self.session.execute(
            select(IncomingEvent).where(IncomingEvent.external_event_id == external_event_id)
        )
        return result.scalar_one_or_none()

    async def mark_processed(self, event: IncomingEvent) -> None:
        event.processing_status = "processed"
        event.processed_at = datetime.now(UTC)
        event.error_message = None
        await self.session.flush()

    async def mark_failed(self, event: IncomingEvent, error: str) -> None:
        event.processing_status = "failed"
        event.processed_at = datetime.now(UTC)
        event.error_message = error
        await self.session.flush()
