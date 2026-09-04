from sqlalchemy.ext.asyncio import AsyncSession
from app.models.game import Game
from app.models.board import Board, BoardType, SortDirection
from app.security import generate_raw_token, hash_value


async def create_game(db: AsyncSession, name: str, api_key: str | None = None) -> tuple[Game, str, str]:
    raw_key = api_key or generate_raw_token()
    raw_secret = generate_raw_token()
    game = Game(name=name, api_key=raw_key, api_secret_hash = hash_value(raw_secret))
    db.add(game)
    await db.flush()
    db.add(Board(game_id=game.id, key="rating", name="Rating", type = BoardType.RATING, sort_direction = SortDirection.DESC))
    await db.commit()

    return game, raw_key, raw_secret