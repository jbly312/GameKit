from toolkit_core.config import ServiceSettings


class Settings(ServiceSettings):
    # TODO: drop this default and require DATABASE_URL from the environment.
    # A default DSN in code silently points a misconfigured deployment at the
    # wrong database. Kept for now because docker-compose relies on it.
    database_url: str = "postgresql+asyncpg://leaderboard:leaderboard@postgres_db:5432/leaderboard"


settings = Settings()
