from app.models.board import Aggregation, Board, BoardType, SortDirection
from app.models.game import Game
from app.models.match import Match
from app.models.player import Player
from app.models.score import Score

# Re-exported so importing app.models registers every table on Base.metadata,
# which is what alembic autogenerate reads.
__all__ = [
    "Aggregation",
    "Board",
    "BoardType",
    "Game",
    "Match",
    "Player",
    "Score",
    "SortDirection",
]
