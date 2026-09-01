from typing import List

from pydantic import BaseModel, Field
from app.models.board import Aggregation, BoardType, SortDirection
from app.models.match import MatchStatus

BOARD_KEY_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,49}$"

class PlayerRegisterRequest(BaseModel):
    device_id: str
    display_name: str | None = None
class PlayerRegisterResponse(BaseModel):
    player_id: int
    player_token: str

class MatchResultRequest(BaseModel):
    winner_id: int
    loser_id: int

class MatchResultResponse(BaseModel):
    match_id: int
    status: MatchStatus
    winner_rating: float| None = None
    loser_rating: float| None = None

class MatchConfirmRequest(BaseModel):
    accept: bool


class BoardCreateRequest(BaseModel):
    key: str = Field(pattern=BOARD_KEY_PATTERN)
    name: str = Field(min_length=1, max_length=100)
    type: BoardType = BoardType.SCORE
    sort_direction: SortDirection = SortDirection.DESC
    aggregation: Aggregation = Aggregation.BEST

class BoardResponse(BaseModel):
    id: int
    key: str
    name: str
    type: BoardType
    sort_direction: SortDirection
    aggregation: Aggregation

    model_config = {"from_attributes": True}

class BoardListResponse(BaseModel):
    items: List[BoardResponse]

class ScoreSubmitRequest(BaseModel):
    value: float

class ScoreSubmitResponse(BaseModel):
    """`value` is what was submitted; `best_value` and `rank` are the player's
    standing on the board afterwards. Both are a snapshot — other players may
    move the rank a moment later.
    """

    score_id: int
    board_key: str
    value: float
    best_value: float
    rank: int

class BoardEntry(BaseModel):
    rank: int
    player_id: int
    display_name: str | None
    value: float

class BoardTopResponse(BaseModel):
    board_key: str
    items: List[BoardEntry]
    limit: int
    offset: int

class BoardMeResponse(BaseModel):
    """`value` and `rank` are null when the player has no result on this board yet."""

    board_key: str
    player_id: int
    display_name: str | None
    value: float | None
    rank: int | None