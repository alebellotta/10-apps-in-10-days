from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EscalationFlag


class EscalationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        thread_id: int,
        message_id: int | None,
        reason: str,
        priority: str,
        operator_summary: str,
        suggested_reply: str | None,
    ) -> EscalationFlag:
        escalation = EscalationFlag(
            thread_id=thread_id,
            message_id=message_id,
            reason=reason,
            priority=priority,
            operator_summary=operator_summary,
            suggested_reply=suggested_reply,
        )
        self.session.add(escalation)
        await self.session.flush()
        return escalation

    async def list_pending(self) -> list[EscalationFlag]:
        result = await self.session.execute(
            select(EscalationFlag).where(EscalationFlag.status == "pending").order_by(desc(EscalationFlag.created_at))
        )
        return list(result.scalars().all())

    async def get_latest_for_thread(self, thread_id: int) -> EscalationFlag | None:
        result = await self.session.execute(
            select(EscalationFlag)
            .where(EscalationFlag.thread_id == thread_id)
            .order_by(desc(EscalationFlag.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def resolve(self, escalation: EscalationFlag) -> None:
        escalation.status = "resolved"
        escalation.resolved_at = datetime.now(UTC)
        await self.session.flush()
