import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column


class Game(Base):
    __tablename__ = 'games'
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    api_key: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        unique=True
        )
    api_secret_hash: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )