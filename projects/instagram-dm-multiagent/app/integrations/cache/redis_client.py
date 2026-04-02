from redis.asyncio import Redis

from app.core.config import get_settings


_client: Redis | None = None


def get_redis_client() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(get_settings().redis_dsn, decode_responses=True)
    return _client
