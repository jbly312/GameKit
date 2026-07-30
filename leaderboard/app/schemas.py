from pydantic import BaseModel

class PlayerRegisterRequest(BaseModel):
    device_id: str

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
