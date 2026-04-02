from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        thread_id: int,
        message_id: int | None,
        action: str,
        actor_type: str,
        actor_name: str,
        payload_json: dict,
    ) -> AuditLog:
        log = AuditLog(
            thread_id=thread_id,
            message_id=message_id,
            action=action,
            actor_type=actor_type,
            actor_name=actor_name,
            payload_json=payload_json,
        )
        self.session.add(log)
        await self.session.flush()
        return log
