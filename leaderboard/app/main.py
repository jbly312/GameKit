from fastapi import FastAPI
from app.routers import players

app = FastAPI(
    title="Leaderboard Service",
    version="0.1.0",
)
app.include_router(players.router)

@app.get("/health")
async def health():
    return {"status": "ok",
            "service": "Leaderboard",
            "version": "0.1.0",
            }