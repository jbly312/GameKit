from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_player

from app.models.player import Player
from app.models.match import Match, MatchStatus
from app.schemas import MatchResultRequest, MatchResultResponse, MatchConfirmRequest
from app.errors import ValidationError, NotAParticipantError, NotFoundError, MatchNotFoundError, MatchExpiredError, MatchAlreadyFinalizedError


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
        raise NotFoundError(
            f"Player with id {set(ids) - players.keys()} not found",
            code="PLAYER_NOT_FOUND",
        )
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

@router.post("/{match_id}/confirm", response_model=MatchResultResponse)
async def confirm_match(
        match_id: int,
        body:MatchConfirmRequest,
        player: Player = Depends(get_current_player),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Match).where(
            Match.id == match_id,
            Match.game_id == player.game_id,
        )
        .with_for_update()
    )
    match = result.scalar_one_or_none()
    if match is None:
        raise MatchNotFoundError(f"Match {match_id} not found")
    if player.id not in (match.winner_id, match.loser_id):
        raise NotAParticipantError("submitter must be a match participant")
    if player.id == match.submitted_by_id:
        raise ValidationError("must be submitted by the second player")

    now = datetime.now(timezone.utc)
    if match.status == MatchStatus.EXPIRED or match.expires_at < now:
        if match.status == MatchStatus.PENDING:
            match.status = MatchStatus.EXPIRED
            await db.commit()
        raise MatchExpiredError(f"Match {match_id} has expired")

    if match.status != MatchStatus.PENDING:
        raise MatchAlreadyFinalizedError("Match already finalized")

    if not body.accept:
        match.status = MatchStatus.DISPUTED
        match.confirmed_by_id = player.id
        match.confirmed_at = now
        await db.commit()
        return MatchResultResponse(match_id=match.id, status=match.status)

    result = await db.execute(
        select(Player)
        .where(Player.id.in_((match.winner_id, match.loser_id)))
        .order_by(Player.id)
        .with_for_update()
    )
    players = {p.id: p for p in result.scalars().all()}
    winner = players[match.winner_id]
    loser = players[match.loser_id]

    winner.rating += RATING_DELTA
    loser.rating -= RATING_DELTA

    match.winner_rating_after = winner.rating
    match.loser_rating_after = loser.rating
    match.status = MatchStatus.CONFIRMED
    match.confirmed_by_id = player.id
    match.confirmed_at = now
    await db.commit()
    return MatchResultResponse(
        match_id=match.id,
        status=match.status,
        winner_rating=match.winner_rating_after,
        loser_rating=match.loser_rating_after
    )