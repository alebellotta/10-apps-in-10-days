import asyncio

from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.cache.redis_client import get_redis_client


logger = get_logger(__name__)


class QueueService:
    _inline_queue: asyncio.Queue[int] | None = None

    def __init__(self) -> None:
        self.settings = get_settings()
        if QueueService._inline_queue is None:
            QueueService._inline_queue = asyncio.Queue()

    async def enqueue_event(self, event_id: int) -> None:
        if self.settings.queue_mode == "inline":
            await QueueService._inline_queue.put(event_id)
            return
        try:
            await get_redis_client().lpush(self.settings.queue_name, event_id)
        except RedisError:
            logger.exception("redis_enqueue_failed", event_id=event_id)
            await self._inline_queue.put(event_id)

    async def dequeue_event(self) -> int | None:
        if self.settings.queue_mode == "inline":
            try:
                return await asyncio.wait_for(
                    QueueService._inline_queue.get(),
                    timeout=self.settings.worker_poll_seconds,
                )
            except TimeoutError:
                return None
        try:
            item = await get_redis_client().brpop(self.settings.queue_name, timeout=int(self.settings.worker_poll_seconds))
            if item:
                return int(item[1])
        except RedisError:
            logger.exception("redis_dequeue_failed")
        return None
