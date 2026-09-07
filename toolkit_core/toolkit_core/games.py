"""Registering a game — the part that is the same everywhere.

Every service keeps its own `games` table in its own database, so every
service needs this. What differs is what else a service sets up alongside the
row: leaderboard adds a rating board, cloudsave will add nothing or something
of its own. That difference goes through `after_create`.
"""

from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from toolkit_core.security import generate_raw_token, hash_value


async def create_game(
    db: AsyncSession,
    game_model,
    name: str,
    api_key: str | None = None,
    after_create: Callable[[AsyncSession, object], Awaitable[None]] | None = None,
) -> tuple[object, str, str]:
    """Create a game and whatever the service needs beside it, atomically.

    Returns the game, its raw api_key and its raw api_secret. Both raw values
    exist only here: the secret is stored hashed and cannot be recovered
    afterwards, so a caller that drops it has destroyed it.

    `api_key` may be supplied to reuse one key across services — a game is
    registered separately in each service's database, and a developer should
    not have to juggle a different key per service.

    The single commit is the point. `flush` gives `game.id` to `after_create`
    without ending the transaction, so a failure there leaves no half-registered
    game behind — which is exactly the state registration exists to prevent.
    """
    raw_key = api_key or generate_raw_token()
    raw_secret = generate_raw_token()

    game = game_model(
        name=name,
        api_key=raw_key,
        api_secret_hash=hash_value(raw_secret),
    )
    db.add(game)
    await db.flush()

    if after_create is not None:
        await after_create(db, game)

    await db.commit()
    return game, raw_key, raw_secret
