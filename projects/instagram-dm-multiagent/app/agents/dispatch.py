from app.db.repositories.audit import AuditLogRepository
from app.services.instagram import InstagramService


class DispatchAgent:
    def __init__(self, instagram_service: InstagramService, audit_logs: AuditLogRepository) -> None:
        self.instagram_service = instagram_service
        self.audit_logs = audit_logs

    async def run(self, thread_id: int, recipient_id: str, text: str) -> dict:
        message, result = await self.instagram_service.send_reply(thread_id=thread_id, recipient_id=recipient_id, text=text)
        await self.audit_logs.create(
            thread_id=thread_id,
            message_id=message.id,
            action="dispatch_sent",
            actor_type="agent",
            actor_name="dispatch",
            payload_json=result,
        )
        return {"message_id": message.id, "provider_response": result}
