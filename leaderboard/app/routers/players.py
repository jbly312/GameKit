from fastapi import APIRouter, Depends, status

from app.database import get_db
from app.schemas import PlayerRegisterRequest,PlayerCredentials, PlayerLoginRequest
from app.dependencies import get_current_game
from app.models import Player
from app.models.game import Game
from app.security import generate_raw_token, hash_value

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.errors import ConflictError, NotFoundError
from sqlalchemy import select


router = APIRouter(prefix="/players", tags=["players"])

@router.post("/register",response_model=PlayerCredentials, status_code=status.HTTP_201_CREATED)
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
    return PlayerCredentials(player_id=player.id, player_token=raw_token)

@router.post("/login",response_model=PlayerCredentials, status_code=status.HTTP_200_OK)
async def login(body:PlayerLoginRequest,
                game: Game = Depends(get_current_game),
                db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(Player)
        .where(
            Player.game_id == game.id,
            Player.device_id == body.device_id,
        )
        .with_for_update()
    )

    player = result.scalar_one_or_none()
    if player is None:
        raise NotFoundError(
            "No player registered for this device",
            code= "PLAYER_NOT_FOUND"
        )
    raw_token = generate_raw_token()
    player.token_hash = hash_value(raw_token)
    await db.commit()

    return PlayerCredentials(player_id=player.id, player_token=raw_token)
