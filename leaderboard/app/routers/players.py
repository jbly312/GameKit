from fastapi import APIRouter, Depends, status
from app.database import get_db
from app.schemas import PlayerRegisterRequest,PlayerRegisterResponse
from app.dependencies import get_current_game
from app.models import Player
from app.models.game import Game
from app.security import generate_raw_token, hash_value
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.errors import ConflictError

router = APIRouter(prefix="/players", tags=["players"])

@router.post("/register",response_model=PlayerRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body:PlayerRegisterRequest,
                   game: Game = Depends(get_current_game),
                   db: AsyncSession = Depends(get_db),):

    raw_token = generate_raw_token()
    token_hash = hash_value(raw_token)

    player = Player(
        game_id = game.id,
        device_id= body.device_id,
        token_hash= token_hash,
        display_name= body.display_name,
    )
    try:
        db.add(player)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ConflictError(
            "Device already registered for this game",
            code="DEVICE_ALREADY_REGISTERED",
        )
    return PlayerRegisterResponse(player_id=player.id, player_token=raw_token)