import os
from app.config import settings
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import  create_async_engine, async_sessionmaker

engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

async def get_db():
        db = AsyncSessionLocal()
        try:
            yield db
        finally:
           await db.close()