import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BoardType(str, enum.Enum):
    """Where the board's values come from.

    SCORE  — players submit values, they are stored in `scores`.
    RATING — values are derived from `players.rating`, moved by confirmed matches.
             Such a board accepts no submissions.
    """

    SCORE = "SCORE"
    RATING = "RATING"


class SortDirection(str, enum.Enum):
    """Which value wins. DESC: higher is better. ASC: lower is better (times)."""

    DESC = "DESC"
    ASC = "ASC"


class Aggregation(str, enum.Enum):
    """How a player's many submissions collapse into a single leaderboard value."""

    BEST = "BEST"
    LAST = "LAST"


class Board(Base):
    __tablename__ = "boards"
    __table_args__ = (
        UniqueConstraint("game_id", "key", name="uq_board_game_key"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("games.id"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    type: Mapped[BoardType] = mapped_column(
        SAEnum(BoardType, create_constraint=True, native_enum=False, length=20),
        nullable=False,
        default=BoardType.SCORE,
    )
    sort_direction: Mapped[SortDirection] = mapped_column(
        SAEnum(SortDirection, create_constraint=True, native_enum=False, length=10),
        nullable=False,
        default=SortDirection.DESC,
    )
    aggregation: Mapped[Aggregation] = mapped_column(
        SAEnum(Aggregation, create_constraint=True, native_enum=False, length=20),
        nullable=False,
        default=Aggregation.BEST,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
