from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from toolkit_core.database import make_engine, make_get_db, make_session_factory

engine = make_engine(settings.database_url)

AsyncSessionLocal = make_session_factory(engine)


class Base(DeclarativeBase):
    """This service's metadata.

    Stays here rather than in toolkit_core: alembic autogenerate reads
    Base.metadata, and a Base shared between services would let one service's
    migration create another service's tables.
    """


get_db = make_get_db(AsyncSessionLocal)
