import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base
from sqlalchemy import String, DateTime, Integer, UniqueConstraint,Float,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("game_id", "device_id"),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id"),
        nullable=False
    )
    device_id: Mapped[str] = mapped_column(
        String,
        nullable=False
    )
    token_hash: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False,
        unique= True
    )
    rating: Mapped[float] = mapped_column(
        Float,
        default=1000,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    display_name: Mapped[str| None] = mapped_column(
        String(50),
        nullable=True
    )