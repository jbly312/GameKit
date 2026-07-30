import uuid
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.database import Base
from sqlalchemy import String, DateTime, Integer, UniqueConstraint,Float,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class Match(Base):
    __tablename__ = 'matches'
    __table_args__ = (
        UniqueConstraint("game_id", "idempotency_key", name="uq_match_game_idempotency"),
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
    winner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id"),
        nullable=False
    )
    loser_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id"),
        nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )
    winner_rating_after: Mapped[float] = mapped_column(
        Float
    )
    loser_rating_after: Mapped[float] = mapped_column(
        Float
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
