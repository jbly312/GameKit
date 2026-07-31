from fastapi import FastAPI
from app.routers import players,matches,leaderboard


app = FastAPI(
    title="Leaderboard Service",
    version="0.1.0",
)
app.include_router(players.router)
app.include_router(matches.router)
app.include_router(leaderboard.router)
@app.get("/health")
async def health():
    return {"status": "ok",
            "service": "Leaderboard",
            "version": "0.1.0",
            }