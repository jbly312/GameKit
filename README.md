# GameKit

Open-source, self-hosted backend services for mobile and indie games.

Each service is a standalone application with its own database. Need only a leaderboard? Deploy just that — nothing else required. Your player data stays in your own infrastructure.

**Status:** early development. The first service, Leaderboard, is functional.

## Leaderboard Service

Player registration, score submission, and ranked leaderboards.

A game defines any number of **boards**. Two kinds exist:

- **Score boards** — players submit values. Sort either way (`DESC` for points, `ASC` for speedrun times) and keep either the player's best or their most recent result.
- **Rating boards** — values come from confirmed 1v1 matches, ±30 points per match. No direct submission.

Both are read through the same endpoints.

- Guest registration by device ID — no passwords, no user accounts
- Duplicate submission protection via `Idempotency-Key`, on both scores and matches
- Correct rating updates under concurrent requests (row-level locking)
- Every attempt is stored, so history survives even though only the aggregate is ranked
- Ties are broken by who got there first, so ranks stay stable across paged requests

## Requirements

- Docker and Docker Compose
- Python 3.14 — only needed to run the test suite

## Quick start

```bash
git clone https://github.com/jbly312/GameKit.git
cd GameKit
cp .env.example .env
docker compose up --build
```

The service starts on `http://localhost:8000` and applies migrations automatically.

Verify it's running:

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "service": "Leaderboard", "version": "0.1.0"}
```

Interactive API docs: http://localhost:8000/docs

## Registering a game

```bash
docker compose exec web python -m app.cli create-game "My Game"
```

```
game_id:    fb6918a3-1a20-468b-b022-2d3499eb7252
api_key:    NGpigW2dJ5lq3HOaOt_afZV1tzvN6_iy-bQcTbbXyw8

api_secret: LOwB684YQr23i2Hi6nmHewXH6zY7KcehpJAQw2vPK-s
This is shown once and cannot be recovered — store it now.
```

The `api_key` goes into the `x-api-key` header on every subsequent request. It is stored in clear and can always be read back from the database.

`api_secret` cannot: only its hash is stored. It is not used by any endpoint yet — it is where privileged operations are headed, since `api_key` has to ship inside the game client and is therefore extractable from the binary.

Registration also creates the game's `rating` board, in the same transaction. A game can never exist without one.

The examples below use `my-api-key` for readability. To follow them verbatim, register with `--api-key my-api-key`.

Running the same game in a second service later? Pass its key so one game keeps one key across the whole toolkit:

```bash
docker compose exec web python -m app.cli create-game "My Game" --api-key NGpigW2d...
```

## Full cycle

### 1. Register players

```bash
curl -X POST http://localhost:8000/players/register \
  -H "x-api-key: my-api-key" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "device-001", "display_name": "Alice"}'
```

```json
{"player_id": 1, "player_token": "ZL-uPeRxrlveh7AIAWIJ5hkDpquA2zeh..."}
```

`player_token` is returned exactly once — only its hash is stored — so the client persists it locally. If it is lost, the device gets a new one from `/players/login`:

```bash
curl -X POST http://localhost:8000/players/login \
  -H "x-api-key: my-api-key" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "device-001"}'
```

```json
{"player_id": 1, "player_token": "9Kt3xNvQ2mHrLpWzYc4Fj7Bd..."}
```

The player keeps their id, name and standing; the previous token stops working. A device the service has never seen gets `404 PLAYER_NOT_FOUND` — the client's cue to register instead.

So a client's startup is: use the stored token; on `401` call `/players/login`; on `404` call `/players/register`.

Register a second player:

```bash
curl -X POST http://localhost:8000/players/register \
  -H "x-api-key: my-api-key" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "device-002", "display_name": "Bob"}'
```

### 2. Create a score board

```bash
curl -X POST http://localhost:8000/boards \
  -H "x-api-key: my-api-key" \
  -H "Content-Type: application/json" \
  -d '{"key": "highscore", "name": "High Score"}'
```

```json
{"id": 2, "key": "highscore", "name": "High Score",
 "type": "SCORE", "sort_direction": "DESC", "aggregation": "BEST"}
```

`sort_direction: "ASC"` makes the lower value better — use it for times. `aggregation: "LAST"` ranks the most recent result instead of the best one.

### 3. Submit a score

```bash
curl -X POST http://localhost:8000/boards/highscore/scores \
  -H "x-api-key: my-api-key" \
  -H "X-Player-Token: ZL-uPeRxrlveh7AIAWIJ5hkDpquA2zeh..." \
  -H "Idempotency-Key: run-0001" \
  -H "Content-Type: application/json" \
  -d '{"value": 4820}'
```

```json
{"score_id": 1, "board_key": "highscore", "value": 4820.0,
 "best_value": 4820.0, "rank": 1}
```

The response carries the player's standing right away, so a game does not need a second request to show "you are 1st" after a run.

Repeating the request with the same `Idempotency-Key` returns the same score without storing it twice. The client generates this key: unique per run, identical across retries. This is what protects the leaderboard when a mobile connection drops mid-request.

### 4. Fetch the top

```bash
curl "http://localhost:8000/boards/highscore/top?limit=10&offset=0" \
  -H "x-api-key: my-api-key"
```

```json
{
  "board_key": "highscore",
  "items": [
    {"rank": 1, "player_id": 1, "display_name": "Alice", "value": 4820.0},
    {"rank": 2, "player_id": 2, "display_name": "Bob", "value": 3110.0}
  ],
  "limit": 10,
  "offset": 0
}
```

`limit` accepts 1–100 and defaults to 50. A player far down the list finds themselves without paging through everything:

```bash
curl http://localhost:8000/boards/highscore/me \
  -H "x-api-key: my-api-key" \
  -H "X-Player-Token: ZL-uPeRxrlveh7AIAWIJ5hkDpquA2zeh..."
```

```json
{"board_key": "highscore", "player_id": 1, "display_name": "Alice",
 "value": 4820.0, "rank": 1}
```

`value` and `rank` are `null` when the player has no result on that board yet.

### 5. Report a 1v1 match

Match results feed the rating board. One participant submits, the other confirms — a result nobody confirms never moves the rating.

```bash
curl -X POST http://localhost:8000/matches/result \
  -H "x-api-key: my-api-key" \
  -H "X-Player-Token: <winner's token>" \
  -H "Idempotency-Key: match-0001" \
  -H "Content-Type: application/json" \
  -d '{"winner_id": 1, "loser_id": 2}'
```

```json
{"match_id": 1, "status": "PENDING", "winner_rating": null, "loser_rating": null}
```

```bash
curl -X POST http://localhost:8000/matches/1/confirm \
  -H "x-api-key: my-api-key" \
  -H "X-Player-Token: <loser's token>" \
  -H "Content-Type: application/json" \
  -d '{"accept": true}'
```

```json
{"match_id": 1, "status": "CONFIRMED", "winner_rating": 1030.0, "loser_rating": 970.0}
```

`{"accept": false}` marks the match `DISPUTED` and leaves both ratings alone. A match that is neither confirmed nor disputed within an hour expires. The result is then read from `/boards/rating/top`, exactly like any other board.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/players/register` | Register a player. Returns `409` if the device is already registered for this game |
| `POST` | `/players/login` | Issue a fresh token for a known `device_id`, revoking the previous one |
| `POST` | `/boards` | Create a board |
| `GET` | `/boards` | List the game's boards |
| `POST` | `/boards/{key}/scores` | Submit a score. Player token, `Idempotency-Key` |
| `GET` | `/boards/{key}/top` | Paginated ranking |
| `GET` | `/boards/{key}/me` | The calling player's value and rank. Player token |
| `POST` | `/matches/result` | Report a 1v1 result. Player token, `Idempotency-Key` |
| `POST` | `/matches/{id}/confirm` | Confirm or dispute a reported result. Player token |

Every endpoint except `/health` requires the `x-api-key` header. An unknown key returns `401`. Endpoints marked "player token" additionally require `X-Player-Token`.

Errors share one envelope:

```json
{"error": {"code": "BOARD_NOT_FOUND", "message": "Board 'highscore' not found"}}
```

## Development

### Layout

```
toolkit_core/    shared infrastructure: settings, engine, error envelope,
                 token hashing, the games table, header auth, registration
leaderboard/     the service
cloudsave/       skeleton, not yet runnable
```

`toolkit_core` deliberately does **not** export a `Base`. Alembic autogenerate reads `Base.metadata`, so a shared one would let a stray import chain make one service's migration create another service's tables. Each service declares its own and composes shared table shapes from mixins.

Because the image needs the package next to the service, the build context is the repository root:

```bash
docker build -f leaderboard/Dockerfile .
```

The repository includes `docker-compose.override.yml` for local development: `leaderboard/` and `toolkit_core/` are both mounted into the container and uvicorn reloads on save. Compose picks the file up automatically — no rebuild needed when editing `.py` files.

### Tests

Tests run against a real PostgreSQL instance. SQLite isn't an option here because the models rely on PostgreSQL-specific types. A separate `leaderboard_test` database is created automatically on first run.

```bash
docker compose up -d db      # the database alone is enough
cd leaderboard
pip install -r requirements.txt
pip install -e ../toolkit_core
pytest -v
```

`toolkit_core` has its own suite, which needs no database:

```bash
cd toolkit_core
pip install -e . -r requirements-dev.txt
pytest -v
```

### Migrations

```bash
cd leaderboard
export DATABASE_URL="postgresql+asyncpg://leaderboard:leaderboard@localhost:5432/leaderboard"
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Built with

FastAPI · SQLAlchemy 2.0 (async) · PostgreSQL 16 · asyncpg · Alembic · Docker Compose · pytest

## Current limitations

Listed deliberately — these are known and scheduled, not overlooked:

- A guest account is exactly as private as its `device_id`. `/players/login` takes nothing else, so whoever knows or guesses a `device_id` takes over that account. Real protection needs an external identity — Play Games or Sign in with Google — which the client can prove after a reinstall; that is not built yet
- No rate limiting — the service is not protected against automated score or rating manipulation, and `/players/login` is a standing invitation to enumerate `device_id`s
- One player is one device. There is no way to sign the same account in on a second device, and no way to merge two of them
- Score values are taken at face value; there is no validation that a result is achievable
- The rating delta is a constant in the source code
- `x-api-key` has to ship inside the game client, where it can be extracted from the binary. Board creation is authorised by that same key, so anyone who extracts it can add boards to your game. `api_secret` is issued for this and not yet enforced
- Registration is a command, not an endpoint — fine for setup, not for a dashboard

Not recommended for production use before v0.2.

## Roadmap

**0.2** — admin operations behind `api_secret`, rate limiting, configurable rating, structured logging

**0.3** — external identity (Sign in with Google) so an account outlives its device, leaderboard caching (Redis), Unity SDK, basic match result validation, pluggable rating algorithms

**1.0** — second service (Cloud Save), matchmaking, project documentation

## License

MIT — see [LICENSE](LICENSE).
