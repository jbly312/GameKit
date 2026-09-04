"""The create-game command, minus the parts a service defines.

A service supplies its own `create_game` and its engine and session factory;
everything error-prone about running async code from a command line lives here.
"""

import asyncio
import sys

from sqlalchemy.exc import IntegrityError


def add_create_game_parser(subparsers):
    parser = subparsers.add_parser(
        "create-game", help="Register a game and print its credentials"
    )
    parser.add_argument("name")
    parser.add_argument(
        "--api-key",
        default=None,
        help="Reuse an existing key so one game shares it across services",
    )
    return parser


async def _create(create_game_fn, engine, session_factory, name, api_key):
    try:
        async with session_factory() as db:
            return await create_game_fn(db, name, api_key)
    finally:
        # The pool holds connections opened inside this event loop. asyncio.run
        # closes the loop on return, and anything left for the garbage collector
        # to clean up afterwards raises "Event loop is closed" at exit.
        await engine.dispose()


def run_create_game(create_game_fn, engine, session_factory, args) -> None:
    try:
        game, api_key, api_secret = asyncio.run(
            _create(create_game_fn, engine, session_factory, args.name, args.api_key)
        )
    except IntegrityError as exc:
        if args.api_key:
            print(f"api_key '{args.api_key}' is already taken", file=sys.stderr)
        else:
            # Do not paraphrase an error nobody diagnosed: IntegrityError also
            # covers not-null, foreign key and check violations, and a confident
            # wrong message sends the reader looking in the wrong place.
            print(f"Could not create the game: {exc.orig}", file=sys.stderr)
        sys.exit(1)

    print(f"game_id:    {game.id}")
    print(f"api_key:    {api_key}")
    print()
    print(f"api_secret: {api_secret}")
    print("This is shown once and cannot be recovered — store it now.")
