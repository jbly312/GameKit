from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_player

from app.models.player import Player
from app.models.match import Match, MatchStatus
from app.schemas import MatchResultRequest, MatchResultResponse
from app.errors import ValidationError, NotAParticipantError, NotFoundError

router = APIRouter(prefix="/matches", tags=["matches"])

RATING_DELTA = 30

@router.post("/result", response_model=MatchResultResponse, status_code=status.HTTP_201_CREATED)
async def submit_match_result(
        body:MatchResultRequest,
        idempotency_key:str = Header(..., alias="idempotency-key"),
        player: Player = Depends(get_current_player),
        db: AsyncSession = Depends(get_db),
):
    if body.winner_id == body.loser_id:
        raise ValidationError("winner_id and loser_id must be different")
    if player.id not in (body.winner_id, body.loser_id):
        raise NotAParticipantError("submitter must be a match participant")
    existing = await db.execute(
        select(Match).where(
            Match.game_id == player.game_id,
            Match.idempotency_key == idempotency_key,
        )
    )
    existing_match = existing.scalar_one_or_none()
    if existing_match is not None:
        return MatchResultResponse(
            match_id=existing_match.id,
            status=existing_match.status,
            winner_rating=existing_match.winner_rating_after,
            loser_rating=existing_match.loser_rating_after,
        )
    ids = (body.winner_id, body.loser_id)
    result = await db.execute(
        select(Player)
        .where(Player.id.in_(ids), Player.game_id == player.game_id)
    )
    players = {p.id: p for p in result.scalars().all()}
    if len(players) != 2:
        raise NotFoundError(f"Player with id {set(ids) - players.keys()} not found")
    winner = players[body.winner_id]
    loser = players[body.loser_id]
    match = Match(
        game_id=player.game_id,
        winner_id=winner.id,
        loser_id=loser.id,
        submitted_by_id=player.id,
        status=MatchStatus.PENDING,
        idempotency_key=idempotency_key,
    )
    db.add(match)
    await db.commit()

    return MatchResultResponse(
        match_id=match.id,
        status=match.status,
    )

