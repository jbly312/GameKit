# GameKit

Open-source, self-hosted backend services for mobile and indie games.

Each service is a standalone application with its own database. Need only a leaderboard? Deploy just that — nothing else required. Your player data stays in your own infrastructure.

**Status:** early development. The first service, Leaderboard, is functional.

## Leaderboard Service

Player registration, match result processing, and ranked leaderboards.

- Guest registration by device ID — no passwords, no user accounts
- Duplicate match protection via `Idempotency-Key`
- Correct rating updates under concurrent requests (row-level locking)
- Rating: fixed ±30 points per match

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

There's no endpoint for this yet — insert the game directly into the database:

```bash
docker compose exec db psql -U leaderboard -d leaderboard -c "
INSERT INTO games (id, name, api_key, api_secret_hash, created_at)
VALUES (gen_random_uuid(), 'My Game', 'my-api-key', 'placeholder', now());
"
```

The `api_key` value goes into the `x-api-key` header on every subsequent request.

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

`player_token` is returned exactly once and cannot be recovered — only its hash is stored. The client must persist it locally.

Register a second player:

```bash
curl -X POST http://localhost:8000/players/register \
  -H "x-api-key: my-api-key" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "device-002", "display_name": "Bob"}'
```

### 2. Submit a match result

```bash
curl -X POST http://localhost:8000/matches/result \
  -H "x-api-key: my-api-key" \
  -H "Idempotency-Key: match-0001" \
  -H "Content-Type: application/json" \
  -d '{"winner_id": 1, "loser_id": 2}'
```

```json
{"match_id": 1, "winner_rating": 1030.0, "loser_rating": 970.0}
```

Repeating the request with the same `Idempotency-Key` returns the same response without applying the rating change again. The client generates this key: it must be unique per match and identical across retries. This is what protects against double-counting when a mobile connection drops mid-request.

### 3. Fetch the leaderboard

```bash
curl "http://localhost:8000/leaderboard?limit=10&offset=0" \
  -H "x-api-key: my-api-key"
```

```json
{
  "items": [
    {"rank": 1, "player_id": 1, "display_name": "Alice", "rating": 1030.0},
    {"rank": 2, "player_id": 2, "display_name": "Bob", "rating": 970.0}
  ],
  "limit": 10,
  "offset": 0
}
```

`limit` accepts 1–100 and defaults to 50.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/players/register` | Register a player. Returns `409` if the device is already registered for this game |
| `POST` | `/matches/result` | Submit a match result. Requires an `Idempotency-Key` header |
| `GET` | `/leaderboard` | Paginated leaderboard |

Every endpoint except `/health` requires the `x-api-key` header. An unknown key returns `401`.

## Development

The repository includes `docker-compose.override.yml` for local development: source code is mounted into the container and uvicorn reloads on save. Compose picks the file up automatically — no rebuild needed when editing `.py` files.

### Tests

Tests run against a real PostgreSQL instance. SQLite isn't an option here because the models rely on PostgreSQL-specific types. A separate `leaderboard_test` database is created automatically on first run.

```bash
docker compose up -d db      # the database alone is enough
cd leaderboard
pip install -r requirements.txt
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

- `player_token` is issued at registration but not yet verified when submitting match results. Requests are authenticated by game API key only
- No rate limiting — the service is not protected against automated rating manipulation
- No endpoint for registering a game; it must be inserted via SQL
- The rating delta is a constant in the source code

Not recommended for production use before v0.2.

## Roadmap

**0.2** — player token verification, rate limiting, game registration endpoint, configurable rating, structured logging

**0.3** — leaderboard caching (Redis), Unity SDK, basic match result validation, pluggable rating algorithms

**1.0** — second service (Economy), matchmaking, shared conventions library, project documentation

## License

MIT — see [LICENSE](LICENSE).
