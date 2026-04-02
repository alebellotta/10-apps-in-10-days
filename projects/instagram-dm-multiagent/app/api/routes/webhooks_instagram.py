from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_meta_signature
from app.db.repositories.events import IncomingEventRepository
from app.db.session import get_db_session
from app.domain.schemas.api import WebhookIngestResponse
from app.integrations.meta.client import MetaClient
from app.services.queue import QueueService


router = APIRouter(prefix="/webhooks/meta/instagram", tags=["instagram-webhooks"])


@router.get("")
async def verify_instagram_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
) -> Response:
    try:
        challenge = MetaClient().verify_webhook(mode=hub_mode, token=hub_verify_token, challenge=hub_challenge)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return Response(content=challenge, media_type="text/plain")


@router.post("", response_model=WebhookIngestResponse)
async def receive_instagram_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    x_hub_signature_256: str | None = Header(default=None),
) -> WebhookIngestResponse:
    body = await request.body()
    if not verify_meta_signature(x_hub_signature_256, body):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = await request.json()
    client = MetaClient()
    events = client.parse_incoming_events(payload)
    event_repo = IncomingEventRepository(session)
    queue = QueueService()
    created_ids: list[int] = []

    for event in events:
        record = await event_repo.create(
            external_event_id=event.external_event_id,
            event_type=event.event_type,
            payload_json=event.model_dump(mode="json"),
        )
        created_ids.append(record.id)
        await queue.enqueue_event(record.id)

    await session.commit()
    return WebhookIngestResponse(status="accepted", event_ids=created_ids)
