
from app.config import settings
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import  create_async_engine, async_sessionmaker

engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session