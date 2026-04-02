from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.orchestration.graph import build_graph
from app.orchestration.state import GraphState


class OrchestrationService:
    def __init__(self, session: AsyncSession) -> None:
        self.settings = get_settings()
        self.graph = build_graph(session)

    async def run(self, state: GraphState) -> GraphState:
        result = await self.graph.ainvoke(state)
        return result
