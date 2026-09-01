from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Score(Base):
    """A single submission. Every attempt is kept; the leaderboard aggregates them."""

    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint("board_id", "idempotency_key", name="uq_score_board_idempotency"),
        Index("ix_score_board_player_value", "board_id", "player_id", "value"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("boards.id"),
        nullable=False,
    )
    player_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("players.id"),
        nullable=False,
    )
    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
