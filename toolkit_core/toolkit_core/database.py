"""Engine and session construction.

Deliberately absent: a shared `Base`.

`alembic revision --autogenerate` reads `Base.metadata`. If two services shared
one Base, the metadata would hold whatever happened to be imported in that
process, and a single stray import chain would make one service's migration
create the other service's tables. It fails late and reads like a mystery.

Each service declares its own `Base`; this module only builds the machinery
around it.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def make_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """`expire_on_commit=False` is load-bearing.

    Callers read attributes off an object after the commit — a CLI printing the
    new game's id, a router building a response. With the default the ORM would
    mark those attributes stale and try to reload them, which is a database
    round trip in a place that has no session open any more.
    """
    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def make_get_db(session_factory: async_sessionmaker[AsyncSession]):
    """FastAPI dependency yielding one session per request."""

    async def get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    return get_db
