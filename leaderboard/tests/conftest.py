import asyncio
import os

import asyncpg
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.game import Game
from app.security import hash_value

TEST_DB_NAME = os.getenv("TEST_DB_NAME","leaderboard_test")
DB_USER = os.getenv("TEST_DB_USER","leaderboard")
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD","leaderboard")
DB_HOST = os.getenv("TEST_DB_HOST","localhost")
DB_PORT = os.getenv("TEST_DB_PORT","5432")

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}"
)
ADMIN_DSN = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"

TEST_API_KEY = "test-api-key"
OTHER_API_KEY = "other-api-key"

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    async def _create():
        conn = await asyncpg.connect(ADMIN_DSN)
        try:
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
            )
            if not exists:
                await conn.execute(f'CREATE DATABASE {TEST_DB_NAME}')
        finally:
            await conn.close()

    asyncio.run(_create())

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def game(db_session):
    g = Game(
        name="Test Game",
        api_key=TEST_API_KEY,
        api_secret_hash=hash_value("test-secret"),
    )
    db_session.add(g)
    await db_session.commit()
    return g


@pytest_asyncio.fixture
async def other_game(db_session):
    g = Game(
        name="Other Game",
        api_key=OTHER_API_KEY,
        api_secret_hash=hash_value("other-secret"),
    )
    db_session.add(g)
    await db_session.commit()
    return g


@pytest.fixture
def auth_headers():
    return {"x-api-key": TEST_API_KEY}


@pytest.fixture
def other_auth_headers():
    return {"x-api-key": OTHER_API_KEY}

async def register(client, headers, device_id, display_name = None):
    r = await client.post('/players/register', headers=headers, json={"device_id": device_id, "display_name": display_name})
    data = r.json()
    return data["player_id"], data["player_token"]


async def submit_match(client, headers, token, winner_id, loser_id, idempotency_key):
    """Submit a match result on behalf of the player owning `token`."""
    return await client.post(
        "/matches/result",
        headers={**headers, "X-Player-Token": token, "Idempotency-Key": idempotency_key},
        json={"winner_id": winner_id, "loser_id": loser_id},
    )


async def confirm_match(client, headers, token, match_id, accept=True):
    """Confirm (or dispute) a match on behalf of the player owning `token`."""
    return await client.post(
        f"/matches/{match_id}/confirm",
        headers={**headers, "X-Player-Token": token},
        json={"accept": accept},
    )


async def play_match(client, headers, winner, loser, idempotency_key):
    """Full happy path: the winner submits, the loser confirms.

    `winner` and `loser` are (player_id, player_token) pairs as returned by register().
    Returns the confirm response.
    """
    winner_id, winner_token = winner
    loser_id, loser_token = loser
    submitted = await submit_match(
        client, headers, winner_token, winner_id, loser_id, idempotency_key
    )
    return await confirm_match(
        client, headers, loser_token, submitted.json()["match_id"], accept=True
    )
