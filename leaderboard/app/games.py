from sqlalchemy.ext.asyncio import AsyncSession

from app.models.board import Board, BoardType, SortDirection
from app.models.game import Game
from toolkit_core.games import create_game as create_game_core


async def _add_rating_board(db: AsyncSession, game: Game) -> None:
    """Leaderboard's half of registration.

    Every game owns a rating board; without it the 1v1 rating has no endpoint
    to be read from. It is added inside the registration transaction, so a game
    can never exist without one.
    """
    db.add(
        Board(
            game_id=game.id,
            key="rating",
            name="Rating",
            type=BoardType.RATING,
            sort_direction=SortDirection.DESC,
        )
    )


async def create_game(
    db: AsyncSession, name: str, api_key: str | None = None
) -> tuple[Game, str, str]:
    """Register a game. Returns it with its raw api_key and api_secret."""
    return await create_game_core(
        db, Game, name, api_key=api_key, after_create=_add_rating_board
    )
