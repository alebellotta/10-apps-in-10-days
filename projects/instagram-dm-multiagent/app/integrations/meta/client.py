from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.meta.schemas import NormalizedInstagramEvent
from app.integrations.meta.verifier import verify_webhook


logger = get_logger(__name__)


class MetaClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        return verify_webhook(mode, token, challenge)

    def parse_incoming_events(self, payload: dict[str, Any]) -> list[NormalizedInstagramEvent]:
        events: list[NormalizedInstagramEvent] = []
        for entry in payload.get("entry", []):
            for messaging in entry.get("messaging", []):
                message = messaging.get("message") or {}
                sender = messaging.get("sender") or {}
                recipient = messaging.get("recipient") or {}
                text = message.get("text")
                if not text:
                    continue
                message_id = message.get("mid", self._stable_hash(messaging))
                sender_id = str(sender.get("id", "unknown_sender"))
                recipient_id = str(recipient.get("id", "unknown_recipient"))
                thread_external_id = f"{recipient_id}:{sender_id}"
                events.append(
                    NormalizedInstagramEvent(
                        external_event_id=message_id,
                        thread_external_id=thread_external_id,
                        message_external_id=message_id,
                        sender_id=sender_id,
                        recipient_id=recipient_id,
                        text=text,
                        raw_payload=messaging,
                    )
                )
        return events

    async def send_dm_reply(self, recipient_id: str, text: str) -> dict[str, Any]:
        if not self.settings.meta_page_access_token:
            logger.info("meta_send_stubbed", recipient_id=recipient_id, text=text)
            return {"status": "stubbed", "recipient_id": recipient_id, "text": text}

        url = (
            f"{self.settings.meta_api_base_url}/{self.settings.meta_graph_api_version}/me/messages"
            f"?access_token={self.settings.meta_page_access_token}"
        )
        payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            logger.info("meta_send_success", recipient_id=recipient_id, response=data)
            return data

    async def mark_message_status(self, message_id: str, status: str) -> dict[str, Any]:
        logger.info("meta_mark_status", message_id=message_id, status=status)
        return {"message_id": message_id, "status": status}

    @staticmethod
    def _stable_hash(payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
