"""Table shapes shared between services, as mixins.

Not as model classes: a SQLAlchemy model binds to its `Base` when the class is
defined, so one class cannot serve two services with separate Bases. A mixin
carries the columns and each service composes its own model:

    class Game(GameMixin, Base):
        __tablename__ = "games"

Each service then owns that table in its own database, with the same shape.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class GameMixin:
    """A game: the tenant every other row belongs to.

    `api_key` is stored in clear because it is looked up on every request and
    is not a secret from the game's own client. `api_secret_hash` holds only a
    hash — the secret is shown once at registration and never recoverable.
    """

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
        unique=True,
    )
    api_secret_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
