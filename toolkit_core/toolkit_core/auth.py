

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toolkit_core.errors import UnauthorizedGameError, UnauthorizedPlayerError
from toolkit_core.security import hash_value


def make_get_current_game(game_model, get_db):
    """Authenticates the game by its `x-api-key` header."""

    async def get_current_game(
        x_api_key: str = Header(...),
        db: AsyncSession = Depends(get_db),
    ):
        result = await db.execute(
            select(game_model).where(game_model.api_key == x_api_key)
        )
        game = result.scalar_one_or_none()
        if game is None:
            raise UnauthorizedGameError("Invalid or missing API key")
        return game

    return get_current_game


def make_get_current_player(player_model, get_db, get_current_game):


    async def get_current_player(
        x_player_token: str = Header(...),
        game=Depends(get_current_game),
        db: AsyncSession = Depends(get_db),
    ):
        token_hash = hash_value(x_player_token)
        result = await db.execute(
            select(player_model).where(
                player_model.token_hash == token_hash,
                player_model.game_id == game.id,
            )
        )
        player = result.scalar_one_or_none()
        if player is None:
            raise UnauthorizedPlayerError("Invalid player token")
        return player

    return get_current_player
