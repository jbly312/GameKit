from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.board_queries import player_standing, top_statement, values_subquery
from app.database import get_db
from app.dependencies import get_current_game, get_current_player
from app.errors import (
    BoardAlreadyExistsError,
    BoardNotFoundError,
    BoardTypeMismatchError,
    ConflictError,
)
from app.models.board import Board, BoardType
from app.models.game import Game
from app.models.player import Player
from app.models.score import Score
from app.schemas import (
    BoardCreateRequest,
    BoardEntry,
    BoardListResponse,
    BoardMeResponse,
    BoardResponse,
    BoardTopResponse,
    ScoreSubmitRequest,
    ScoreSubmitResponse,
)

router = APIRouter(prefix="/boards", tags=["boards"])


async def _get_board(db: AsyncSession, game_id, key: str) -> Board:
    result = await db.execute(
        select(Board).where(Board.game_id == game_id, Board.key == key)
    )
    board = result.scalar_one_or_none()
    if board is None:
        raise BoardNotFoundError(f"Board '{key}' not found")
    return board


@router.post("", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    body: BoardCreateRequest,
    game: Game = Depends(get_current_game),
    db: AsyncSession = Depends(get_db),
):
    board = Board(
        game_id=game.id,
        key=body.key,
        name=body.name,
        type=body.type,
        sort_direction=body.sort_direction,
        aggregation=body.aggregation,
    )
    try:
        db.add(board)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise BoardAlreadyExistsError(f"Board '{body.key}' already exists for this game")
    return BoardResponse.model_validate(board)


@router.get("", response_model=BoardListResponse)
async def list_boards(
    game: Game = Depends(get_current_game),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Board).where(Board.game_id == game.id).order_by(Board.id.asc())
    )
    return BoardListResponse(
        items=[BoardResponse.model_validate(b) for b in result.scalars().all()]
    )


@router.post(
    "/{key}/scores",
    response_model=ScoreSubmitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_score(
    key: str,
    body: ScoreSubmitRequest,
    idempotency_key: str = Header(..., alias="idempotency-key"),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    board = await _get_board(db, player.game_id, key)
    if board.type != BoardType.SCORE:
        raise BoardTypeMismatchError(
            f"Board '{key}' has type {board.type.value} and accepts no submissions"
        )

    # Held as plain values: a rollback below expires every ORM object in the
    # session, and touching an expired attribute afterwards triggers lazy IO.
    board_id = board.id
    player_id = player.id

    score = await _score_for_key(db, board_id, idempotency_key)
    if score is None:
        score = Score(
            board_id=board_id,
            player_id=player_id,
            value=body.value,
            idempotency_key=idempotency_key,
        )
        db.add(score)
        try:
            await db.commit()
        except IntegrityError:
            # A concurrent retry with the same key won the race. That is exactly
            # what the key is for, so read its row and answer as if we wrote it.
            await db.rollback()
            board = await db.get(Board, board_id)
            score = await _score_for_key(db, board_id, idempotency_key)
            if score is None:
                raise
    _reject_foreign_key_owner(score, player_id)

    best_value, rank = await player_standing(db, board, player_id)
    return ScoreSubmitResponse(
        score_id=score.id,
        board_key=board.key,
        value=score.value,
        best_value=best_value,
        rank=rank,
    )


async def _score_for_key(db: AsyncSession, board_id: int, idempotency_key: str):
    result = await db.execute(
        select(Score).where(
            Score.board_id == board_id,
            Score.idempotency_key == idempotency_key,
        )
    )
    return result.scalar_one_or_none()


def _reject_foreign_key_owner(score: Score, player_id: int) -> None:
    """Idempotency keys are unique per board, so two players can collide on one.

    Replaying someone else's key must not hand their result back to the caller.
    """
    if score.player_id != player_id:
        raise ConflictError(
            "Idempotency key already used by another player",
            code="IDEMPOTENCY_KEY_CONFLICT",
        )


@router.get("/{key}/top", response_model=BoardTopResponse)
async def get_top(
    key: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    game: Game = Depends(get_current_game),
    db: AsyncSession = Depends(get_db),
):
    board = await _get_board(db, game.id, key)
    values = values_subquery(board)
    rows = await db.execute(top_statement(board, values, limit, offset))

    items = [
        BoardEntry(
            rank=rank,
            player_id=row.player_id,
            display_name=row.display_name,
            value=row.value,
        )
        for rank, row in enumerate(rows.all(), start=offset + 1)
    ]
    return BoardTopResponse(
        board_key=board.key, items=items, limit=limit, offset=offset
    )


@router.get("/{key}/me", response_model=BoardMeResponse)
async def get_my_standing(
    key: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    board = await _get_board(db, player.game_id, key)
    value, rank = await player_standing(db, board, player.id)
    return BoardMeResponse(
        board_key=board.key,
        player_id=player.id,
        display_name=player.display_name,
        value=value,
        rank=rank,
    )
