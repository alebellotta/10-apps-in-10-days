from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.domain.schemas.common import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
        llm_model=settings.openai_model,
        timestamp=datetime.now(UTC),
    )
