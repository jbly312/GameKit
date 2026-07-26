from fastapi import FastAPI

app = FastAPI(
    title="Leaderboard Service",
    version="0.1.0",
)

@app.get("/health")
async def health():
    return {"status": "ok",
            "service": "Leaderboard",
            "version": "0.1.0",
            }