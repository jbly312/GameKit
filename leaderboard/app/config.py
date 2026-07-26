from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://leaderboard:leaderboard@postgres_db:5432/leaderboard"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()