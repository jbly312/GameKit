from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from app.routers import players,matches,leaderboard
from app.errors import ToolkitError
from fastapi.exceptions import RequestValidationError


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

@app.exception_handler(ToolkitError)
async def toolkit_error_handler(request: Request, exc: ToolkitError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )