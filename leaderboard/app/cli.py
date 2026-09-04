import argparse
import asyncio
import sys

from sqlalchemy.exc import IntegrityError

from app.database import AsyncSessionLocal, engine
from app.games import create_game
parser = argparse.ArgumentParser(prog="api.cli")
sub = parser.add_subparsers(dest="command", required=True)

create = sub.add_parser("create-game", help= "Register a game and its rating board" )
create.add_argument("name")
create.add_argument("--api-key", default=None, help="Reuse an existing key so one game shares it across services")

async def create_game_command(name, api_key):
    try:
        async with AsyncSessionLocal() as db:
            return await create_game(db, name, api_key)
    finally:
        await engine.dispose()

def main():
    args = parser.parse_args()
    if args.command == "create-game":
        try:
            game, key, secret = asyncio.run(create_game_command(args.name, args.api_key))
        except IntegrityError as exc:
            if args.api_key:
                print(f"api_key'{args.api_key}' is already taken", file = sys.stderr)
            else:
                print(f"Could not create the game: {exc.orig}", file=sys.stderr)
            sys.exit(1)

        print(f"game_id:    {game.id}")
        print(f"api_key:    {key}")
        print()
        print(f"api_secret: {secret}")
        print("This is shown once and cannot be recovered — store it now.")

if __name__ == "__main__":
    main()