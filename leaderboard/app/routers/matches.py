from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_game
from app.models.game import Game
from app.models.player import Player
from app.models.match import Match
from app.schemas import MatchResultRequest, MatchResultResponse

router = APIRouter(prefix="/matches", tags=["matches"])

RATING_DELTA = 30

@router.post("/result", response_model=MatchResultResponse, status_code=status.HTTP_201_CREATED)
async def submit_match_result(
        body:MatchResultRequest,
        idempotency_key:str = Header(..., alias="idempotency-key"),
        game: Game = Depends(get_current_game),
        db: AsyncSession = Depends(get_db),
):
    if body.winner_id == body.loser_id:
        raise HTTPException(status_code=400, detail="winner_id and loser_id must be different")
    existing = await db.execute(
        select(Match).where(
            Match.game_id == game.id,
            Match.idempotency_key == idempotency_key,
        )
    )
    existing_match = existing.scalar_one_or_none()
    if existing_match is not None:
        return MatchResultResponse(
            match_id=existing_match.id,
            winner_rating=existing_match.winner_rating_after,
            loser_rating=existing_match.loser_rating_after,
        )
    ordered_ids = sorted([body.winner_id, body.loser_id])
    result = await db.execute(
        select(Player)
        .where(Player.id.in_(ordered_ids), Player.game_id == game.id)
        .with_for_update()
        .order_by(Player.id)
    )
    players = {p.id: p for p in result.scalars().all()}

    if body.winner_id not in players or body.loser_id not in players:
        raise HTTPException(status_code=404, detail="Player not found")

    winner = players[body.winner_id]
    loser = players[body.loser_id]

    winner.rating += RATING_DELTA
    loser.rating -= RATING_DELTA
    match = Match(
        game_id=game.id,
        winner_id=winner.id,
        loser_id=loser.id,
        idempotency_key=idempotency_key,
        winner_rating_after=winner.rating,
        loser_rating_after=loser.rating,
    )
    db.add(match)
    await db.commit()

    return MatchResultResponse(
        match_id=match.id,
        winner_rating=winner.rating,
        loser_rating=loser.rating,
    )