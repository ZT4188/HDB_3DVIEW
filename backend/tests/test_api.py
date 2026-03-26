"""
Basic API tests for HDB 3D Simulation backend.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "postgresql+asyncpg://hdb3d:testpass@localhost:5432/hdb3d_test"

test_engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_buildings_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/buildings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert isinstance(data["features"], list)


@pytest.mark.asyncio
async def test_create_and_list_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create session
        resp = await client.post("/sessions?name=Test+Run")
        assert resp.status_code == 200
        session = resp.json()
        assert session["name"] == "Test Run"
        assert session["current_year"] == 2025

        # List sessions
        resp = await client.get("/sessions")
        assert resp.status_code == 200
        sessions = resp.json()
        assert len(sessions) == 1
        assert sessions[0]["id"] == session["id"]


@pytest.mark.asyncio
async def test_delete_session():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/sessions?name=To+Delete")
        sid = resp.json()["id"]

        resp = await client.delete(f"/sessions/{sid}")
        assert resp.status_code == 200

        resp = await client.get("/sessions")
        assert len(resp.json()) == 0


@pytest.mark.asyncio
async def test_get_nonexistent_building():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/buildings/nonexistent-id")
    assert resp.status_code == 404
