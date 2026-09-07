from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):


    database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
