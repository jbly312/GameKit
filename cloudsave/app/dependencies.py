from fastapi import Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.game import Game
from app.models.player import Player
from app.errors import UnauthorizedPlayerError, UnauthorizedGameError

from app.security import hash_value


async def get_current_game(
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Game:
    result = await db.execute(select(Game).where(Game.api_key == x_api_key))
    game = result.scalar_one_or_none()
    if game is None:
        raise UnauthorizedGameError("Invalid or missing API key")
    else:
        return game

async def get_current_player(
        x_player_token: str = Header(...),
        game: Game = Depends(get_current_game),
        db: AsyncSession = Depends(get_db),
) -> Player:
    token_hash = hash_value(x_player_token)
    result = await db.execute(
        select(Player).where(
            Player.token_hash == token_hash,
            Player.game_id == game.id,
        )
    )
    player = result.scalar_one_or_none()
    if player is None:
        raise UnauthorizedPlayerError("Invalid player token")
    return player
