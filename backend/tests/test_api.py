import pytest
from httpx import ASGITransport, AsyncClient
import sqlalchemy as sa

from app.database import get_db
from app.models import Base
from app.main import app

_test_db_url = "sqlite+aiosqlite:///./test_spanish.db"
_test_engine = sa.ext.asyncio.create_async_engine(_test_db_url, echo=False)
_test_session = sa.ext.asyncio.async_sessionmaker(
    _test_engine, class_=sa.ext.asyncio.AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with _test_session() as session:
        yield session


async def seed_test_db():
    from app.crud import seed_database
    async with _test_session() as db:
        await seed_database(db)


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_user(client):
    resp = await client.post("/api/users/register", json={"telegram_id": 12345, "username": "testuser"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["telegram_id"] == 12345
    assert data["current_level"] == "A0"
    assert data["placement_complete"] is False


@pytest.mark.asyncio
async def test_user_progress(client):
    await client.post("/api/users/register", json={"telegram_id": 99999, "username": "progresstest"})
    resp = await client.get("/api/users/1/progress")
    assert resp.status_code == 200
    data = resp.json()
    assert "level" in data
    assert "xp" in data
    assert "streak" in data


@pytest.mark.asyncio
async def test_placement_question(client):
    resp = await client.get("/api/placement/question/0")
    assert resp.status_code == 200
    data = resp.json()
    assert "spanish" in data
    assert "options" in data


@pytest.mark.asyncio
async def test_placement_evaluate(client):
    answers = [
        {"question_id": 0, "chosen_index": 1, "response_time_ms": 2000},
        {"question_id": 1, "chosen_index": 0, "response_time_ms": 1500},
        {"question_id": 2, "chosen_index": 2, "response_time_ms": 3000},
        {"question_id": 3, "chosen_index": 0, "response_time_ms": 2500},
        {"question_id": 4, "chosen_index": 1, "response_time_ms": 1800},
        {"question_id": 5, "chosen_index": 2, "response_time_ms": 2200},
        {"question_id": 6, "chosen_index": 1, "response_time_ms": 1500},
        {"question_id": 7, "chosen_index": 1, "response_time_ms": 3000},
        {"question_id": 8, "chosen_index": 1, "response_time_ms": 2000},
        {"question_id": 9, "chosen_index": 1, "response_time_ms": 2500},
    ]
    resp = await client.post("/api/placement/evaluate", json=answers)
    assert resp.status_code == 200
    data = resp.json()
    assert "assigned_level" in data
    assert "score" in data


@pytest.mark.asyncio
async def test_seed_data(client):
    await seed_test_db()
    resp = await client.get("/api/lessons/list?user_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_grammar_points(client):
    await seed_test_db()
    resp = await client.get("/api/conversation/grammar?level=A0")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_vocab_due_empty(client):
    resp = await client.get("/api/vocab/due?user_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_conversation_context(client):
    await client.post("/api/users/register", json={"telegram_id": 77777, "username": "convo"})
    resp = await client.get("/api/conversation/context?user_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "level" in data
    assert "known_words_sample" in data


@pytest.mark.asyncio
async def test_stats(client):
    await client.post("/api/users/register", json={"telegram_id": 88888, "username": "stats"})
    resp = await client.get("/api/conversation/stats?user_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "level" in data
    assert "total_words_learned" in data
