from pydantic import BaseModel

class PlayerRegisterRequest(BaseModel):
    device_id: str

class PlayerRegisterResponse(BaseModel):
    player_id: int
    player_token: str