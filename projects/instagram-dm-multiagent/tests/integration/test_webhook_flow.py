import asyncio

import pytest

from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.events import IncomingEventRepository
from app.db.repositories.escalations import EscalationRepository
from app.workers.processor import EventProcessor


@pytest.mark.asyncio
async def test_webhook_to_escalation_flow(client, session_factory):
    payload = {
        "entry": [
            {
                "messaging": [
                    {
                        "sender": {"id": "user-123"},
                        "recipient": {"id": "brand-1"},
                        "message": {"mid": "m-1", "text": "Voglio un rimborso"},
                    }
                ]
            }
        ]
    }
    response = await client.post("/webhooks/meta/instagram", json=payload)
    assert response.status_code == 200
    event_id = response.json()["event_ids"][0]

    async with session_factory() as session:
        await EventProcessor(session).process_event(event_id)

    async with session_factory() as session:
        threads = await ConversationRepository(session).list_threads()
        escalations = await EscalationRepository(session).list_pending()
        assert len(threads) == 1
        assert len(escalations) == 1


@pytest.mark.asyncio
async def test_dashboard_thread_detail(client, session_factory):
    payload = {
        "entry": [
            {
                "messaging": [
                    {
                        "sender": {"id": "user-999"},
                        "recipient": {"id": "brand-1"},
                        "message": {"mid": "m-2", "text": "Quali sono gli orari?"},
                    }
                ]
            }
        ]
    }
    response = await client.post("/webhooks/meta/instagram", json=payload)
    event_id = response.json()["event_ids"][0]
    async with session_factory() as session:
        await EventProcessor(session).process_event(event_id)
    threads_response = await client.get("/threads")
    thread_id = threads_response.json()[0]["id"]
    detail_response = await client.get(f"/dashboard/threads/{thread_id}")
    assert detail_response.status_code == 200
    assert "Thread" in detail_response.text
