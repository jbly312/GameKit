from typing import List

from pydantic import BaseModel

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
    winner_rating: float
    loser_rating: float

class LeaderboardEntry(BaseModel):
    rank: int
    player_id: int
    display_name: str | None
    rating: float

class LeaderboardResponse(BaseModel):
    items: List[LeaderboardEntry]
    limit: int
    offset: int