import argparse

from app.database import AsyncSessionLocal, engine
from app.games import create_game
from toolkit_core.cli import add_create_game_parser, run_create_game

parser = argparse.ArgumentParser(prog="app.cli")
sub = parser.add_subparsers(dest="command", required=True)
add_create_game_parser(sub)


def main():
    args = parser.parse_args()
    if args.command == "create-game":
        run_create_game(create_game, engine, AsyncSessionLocal, args)


if __name__ == "__main__":
    main()
