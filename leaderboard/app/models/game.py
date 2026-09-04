from app.database import Base
from toolkit_core.models import GameMixin


class Game(GameMixin, Base):
    """Same shape in every service, bound to this service's metadata."""

    __tablename__ = "games"
