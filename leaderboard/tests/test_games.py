"""Game registration.

These tests cover the function, not the CLI: the CLI only parses arguments and
prints, so everything worth guarding lives in create_game.
"""

import pytest
from sqlalchemy import select

from app import games as games_module
from app.games import create_game
from app.models.board import Board, BoardType, SortDirection
from app.models.game import Game
from app.security import hash_value
from tests.conftest import board_top


async def test_registration_creates_the_rating_board(client, db_session):
    game, _, _ = await create_game(db_session, "My Game")

    board = (
        await db_session.execute(select(Board).where(Board.game_id == game.id))
    ).scalar_one()

    assert board.key == "rating"
    assert board.type == BoardType.RATING
    assert board.sort_direction == SortDirection.DESC


async def test_returned_key_authenticates(client, db_session):
    """The point of the whole command: the printed key works immediately."""
    _, api_key, _ = await create_game(db_session, "My Game")

    r = await board_top(client, {"x-api-key": api_key}, "rating")

    assert r.status_code == 200
    assert r.json()["items"] == []


async def test_supplied_key_is_used_as_is(client, db_session):
    """One key has to span services, so a caller-provided one must survive."""
    game, api_key, _ = await create_game(db_session, "My Game", api_key="shared-key")

    assert api_key == "shared-key"
    assert game.api_key == "shared-key"


async def test_generated_keys_differ(client, db_session):
    _, first_key, _ = await create_game(db_session, "First")
    _, second_key, _ = await create_game(db_session, "Second")

    assert first_key != second_key


async def test_secret_is_stored_only_as_a_hash(client, db_session):
    """The returned secret is the only copy; the row must not hold it in clear."""
    game, _, secret = await create_game(db_session, "My Game")

    assert game.api_secret_hash != secret
    assert game.api_secret_hash == hash_value(secret)


async def test_game_is_not_left_behind_when_the_board_fails(
    client, db_session, monkeypatch
):
    """Game and board are one transaction.

    If the board can fail after the game is already committed, registration
    produces exactly the broken state it exists to prevent: a game whose rating
    has no endpoint.
    """

    def exploding_board(*args, **kwargs):
        raise RuntimeError("board creation failed")

    monkeypatch.setattr(games_module, "Board", exploding_board)

    with pytest.raises(RuntimeError):
        await create_game(db_session, "My Game")

    await db_session.rollback()

    assert (await db_session.execute(select(Game))).scalars().all() == []
    assert (await db_session.execute(select(Board))).scalars().all() == []
