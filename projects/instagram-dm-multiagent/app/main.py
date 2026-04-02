from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import dashboard, escalations, health, kb, threads, webhooks_instagram
from app.core.config import BASE_DIR
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import init_db
from app.workers.processor import WorkerRuntime


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    await init_db()

    worker = WorkerRuntime()
    await worker.start()
    app.state.worker = worker
    get_logger(__name__).info("application_started", env=settings.app_env)
    try:
        yield
    finally:
        await worker.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="Instagram DM Multi-Agent MVP", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "dashboard" / "static")), name="static")
    app.include_router(health.router)
    app.include_router(webhooks_instagram.router)
    app.include_router(threads.router)
    app.include_router(escalations.router)
    app.include_router(kb.router)
    app.include_router(dashboard.router)
    return app


app = create_app()
