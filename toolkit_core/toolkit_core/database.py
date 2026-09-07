

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

    return async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def make_get_db(session_factory: async_sessionmaker[AsyncSession]):

    async def get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    return get_db
