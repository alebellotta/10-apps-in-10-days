from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KnowledgeBaseEntry


class KnowledgeBaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[KnowledgeBaseEntry]:
        result = await self.session.execute(select(KnowledgeBaseEntry).order_by(KnowledgeBaseEntry.id))
        return list(result.scalars().all())

    async def create(self, **kwargs) -> KnowledgeBaseEntry:
        entry = KnowledgeBaseEntry(**kwargs)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get(self, kb_id: int) -> KnowledgeBaseEntry | None:
        result = await self.session.execute(select(KnowledgeBaseEntry).where(KnowledgeBaseEntry.id == kb_id))
        return result.scalar_one_or_none()

    async def update(self, kb_id: int, **kwargs) -> KnowledgeBaseEntry | None:
        entry = await self.get(kb_id)
        if entry is None:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(entry, key, value)
        await self.session.flush()
        return entry

    async def delete(self, kb_id: int) -> bool:
        entry = await self.get(kb_id)
        if entry is None:
            return False
        await self.session.delete(entry)
        await self.session.flush()
        return True

    async def search(self, query: str, language: str, limit: int = 5) -> list[KnowledgeBaseEntry]:
        pattern = f"%{query.lower()}%"
        result = await self.session.execute(
            select(KnowledgeBaseEntry)
            .where(
                KnowledgeBaseEntry.is_active.is_(True),
                KnowledgeBaseEntry.language == language,
                or_(
                    KnowledgeBaseEntry.question.ilike(pattern),
                    KnowledgeBaseEntry.answer.ilike(pattern),
                    KnowledgeBaseEntry.tags.ilike(pattern),
                ),
            )
            .limit(limit)
        )
        return list(result.scalars().all())
