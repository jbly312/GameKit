from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    """Settings every service has.

    `database_url` is declared without a default on purpose: a default DSN in
    code silently points a misconfigured deployment at some other service's
    database. A service may still override it with a default of its own while
    it is convenient — but the base does not hand one out.
    """

    database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
