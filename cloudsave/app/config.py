from pydantic_settings import BaseSettings,SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cloudsave:cloudsave@postgres_db:5432/cloudsave"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()