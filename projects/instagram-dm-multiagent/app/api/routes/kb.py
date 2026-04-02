from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import enforce_internal_rate_limit
from app.db.repositories.kb import KnowledgeBaseRepository
from app.db.session import get_db_session
from app.domain.schemas.api import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate


router = APIRouter(tags=["knowledge-base"], dependencies=[Depends(enforce_internal_rate_limit)])


@router.get("/kb", response_model=list[KnowledgeBaseRead])
async def list_kb(session: AsyncSession = Depends(get_db_session)) -> list[KnowledgeBaseRead]:
    items = await KnowledgeBaseRepository(session).list_all()
    return [KnowledgeBaseRead.model_validate(item) for item in items]


@router.post("/kb", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_kb(payload: KnowledgeBaseCreate, session: AsyncSession = Depends(get_db_session)) -> KnowledgeBaseRead:
    item = await KnowledgeBaseRepository(session).create(**payload.model_dump())
    await session.commit()
    return KnowledgeBaseRead.model_validate(item)


@router.patch("/kb/{kb_id}", response_model=KnowledgeBaseRead)
async def update_kb(
    kb_id: int,
    payload: KnowledgeBaseUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> KnowledgeBaseRead:
    item = await KnowledgeBaseRepository(session).update(kb_id, **payload.model_dump())
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")
    await session.commit()
    return KnowledgeBaseRead.model_validate(item)


@router.delete("/kb/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb(kb_id: int, session: AsyncSession = Depends(get_db_session)) -> None:
    deleted = await KnowledgeBaseRepository(session).delete(kb_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KB entry not found")
    await session.commit()
