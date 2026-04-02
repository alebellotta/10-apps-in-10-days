import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"
os.environ["QUEUE_MODE"] = "inline"
os.environ["WORKER_ENABLED"] = "false"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["META_VERIFY_TOKEN"] = "test-token"

import asyncio
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app


TEST_DATABASE_URL = os.environ["DATABASE_URL"]


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def session_factory(tmp_path) -> AsyncIterator[async_sessionmaker]:
    db_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield session_maker
    finally:
        await engine.dispose()


@pytest.fixture()
async def client(session_factory):
    app = create_app()

    async def override_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
