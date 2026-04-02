from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import enforce_internal_rate_limit
from app.db.repositories.escalations import EscalationRepository
from app.db.session import get_db_session
from app.domain.schemas.api import EscalationRead


router = APIRouter(tags=["escalations"], dependencies=[Depends(enforce_internal_rate_limit)])


@router.get("/escalations", response_model=list[EscalationRead])
async def list_escalations(session: AsyncSession = Depends(get_db_session)) -> list[EscalationRead]:
    escalations = await EscalationRepository(session).list_pending()
    return [EscalationRead.model_validate(item) for item in escalations]
