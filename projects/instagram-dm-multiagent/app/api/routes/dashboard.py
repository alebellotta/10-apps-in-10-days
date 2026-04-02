from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.escalations import EscalationRepository
from app.db.session import get_db_session
from app.services.threads import ThreadService


templates = Jinja2Templates(directory="app/dashboard/templates")
router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/threads", response_class=HTMLResponse)
async def dashboard_threads(request: Request, session: AsyncSession = Depends(get_db_session)) -> HTMLResponse:
    threads = await ConversationRepository(session).list_threads()
    escalations = {item.thread_id: item for item in await EscalationRepository(session).list_pending()}
    return templates.TemplateResponse(
        request,
        "threads.html",
        {"threads": threads, "escalations": escalations},
    )


@router.get("/dashboard/threads/{thread_id}", response_class=HTMLResponse)
async def dashboard_thread_detail(request: Request, thread_id: int, session: AsyncSession = Depends(get_db_session)) -> HTMLResponse:
    detail = await ThreadService(session).get_thread_detail(thread_id)
    return templates.TemplateResponse(request, "thread_detail.html", detail)
