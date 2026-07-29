from fastapi import Header, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.game import Game

async def get_current_game(
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Game:
    result = await db.execute(select(Game).where(Game.api_key == x_api_key))
    game = result.scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        return game