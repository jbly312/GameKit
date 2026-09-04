from app.database import get_db
from app.models.game import Game
from app.models.player import Player
from toolkit_core.auth import make_get_current_game, make_get_current_player

get_current_game = make_get_current_game(Game, get_db)
get_current_player = make_get_current_player(Player, get_db, get_current_game)
