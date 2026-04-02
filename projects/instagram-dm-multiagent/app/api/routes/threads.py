from fastapi import APIRouter, Depends, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import enforce_internal_rate_limit
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.events import IncomingEventRepository
from app.db.session import get_db_session
from app.domain.schemas.api import (
    ApproveDraftRequest,
    ConversationRead,
    EscalationRead,
    ManualMessageRequest,
    MessageRead,
    RetryProcessingResponse,
    ThreadDetailResponse,
    UpdateModeRequest,
)
from app.services.queue import QueueService
from app.services.threads import ThreadService


templates = Jinja2Templates(directory="app/dashboard/templates")
router = APIRouter(tags=["threads"], dependencies=[Depends(enforce_internal_rate_limit)])


@router.get("/threads", response_model=list[ConversationRead])
async def list_threads(session: AsyncSession = Depends(get_db_session)) -> list[ConversationRead]:
    threads = await ConversationRepository(session).list_threads()
    return [ConversationRead.model_validate(thread) for thread in threads]


@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(thread_id: int, session: AsyncSession = Depends(get_db_session)) -> ThreadDetailResponse:
    detail = await ThreadService(session).get_thread_detail(thread_id)
    return ThreadDetailResponse(
        thread=ConversationRead.model_validate(detail["thread"]),
        messages=[MessageRead.model_validate(message) for message in detail["messages"]],
        escalation=EscalationRead.model_validate(detail["escalation"]) if detail["escalation"] else None,
        draft=detail["draft"],
        mode=detail["mode"],
        state=detail["state"],
    )


@router.get("/threads/{thread_id}/messages", response_model=list[MessageRead])
async def get_thread_messages(thread_id: int, session: AsyncSession = Depends(get_db_session)) -> list[MessageRead]:
    detail = await ThreadService(session).get_thread_detail(thread_id)
    return [MessageRead.model_validate(message) for message in detail["messages"]]


@router.post("/threads/{thread_id}/approve-draft")
async def approve_draft(
    thread_id: int,
    payload: ApproveDraftRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    result = await ThreadService(session).approve_draft(thread_id, payload.text)
    await session.commit()
    return result


@router.post("/threads/{thread_id}/send-manual-message")
async def send_manual_message(
    thread_id: int,
    payload: ManualMessageRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    result = await ThreadService(session).send_manual_message(thread_id, payload.text)
    await session.commit()
    return result


@router.post("/threads/{thread_id}/retry-processing", response_model=RetryProcessingResponse)
async def retry_processing(thread_id: int, session: AsyncSession = Depends(get_db_session)) -> RetryProcessingResponse:
    detail = await ThreadService(session).get_thread_detail(thread_id)
    inbound = next((message for message in reversed(detail["messages"]) if message.direction == "inbound"), None)
    event = await IncomingEventRepository(session).get_by_external_id(inbound.external_message_id if inbound else "")
    if event is None:
        event = await IncomingEventRepository(session).create(
            external_event_id=f"retry-{thread_id}",
            event_type="manual_retry",
            payload_json={
                "external_event_id": f"retry-{thread_id}",
                "thread_external_id": detail["thread"].thread_external_id,
                "message_external_id": inbound.external_message_id if inbound else f"retry-message-{thread_id}",
                "sender_id": inbound.sender_id if inbound else detail["thread"].user_external_id,
                "recipient_id": inbound.recipient_id if inbound else "brand",
                "text": inbound.text if inbound else "",
                "raw_payload": {},
            },
        )
    await QueueService().enqueue_event(event.id)
    await session.commit()
    return RetryProcessingResponse(status="queued", event_id=event.id)


@router.patch("/threads/{thread_id}/mode")
async def update_thread_mode(
    thread_id: int,
    payload: UpdateModeRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    conversation = await ConversationRepository(session).update_mode(thread_id, payload.mode)
    await session.commit()
    if conversation is None:
        return {"status": "not_found"}
    return {"status": "updated", "mode": payload.mode}
