from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_game
from app.models.game import Game
from app.models.player import Player
from app.schemas import LeaderboardEntry, LeaderboardResponse


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])

@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    game: Game = Depends(get_current_game),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Player)
        .where(Player.game_id == game.id)
        .order_by(Player.rating.desc(), Player.id.asc())
        .limit(limit)
        .offset(offset)
    )
    players_result = result.scalars().all()

    items = []
    for rank, player in enumerate(players_result, start=offset + 1):
        items.append(
            LeaderboardEntry(
                rank=rank,
                player_id=player.id,
                display_name=player.display_name,
                rating=player.rating,
            )
        )

    return LeaderboardResponse(items=items, offset=offset, limit=limit)


