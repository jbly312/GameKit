import uuid
import enum

from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone, timedelta
from app.database import Base
from sqlalchemy import String, DateTime, Integer, UniqueConstraint,Float,ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SAEnum
MATCH_TTL = timedelta(hours=1)
class MatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DISPUTED = "DISPUTED"
    EXPIRED = "EXPIRED"

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
    winner_rating_after: Mapped[float| None] = mapped_column(
        Float
    )
    loser_rating_after: Mapped[float| None] = mapped_column(
        Float
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus, create_constraint=True, native_enum=False, length=20),
        default=MatchStatus.PENDING,
        nullable=False,
        index=True,
    )
    submitted_by_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False)
    confirmed_by_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + MATCH_TTL,
        nullable=False,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )