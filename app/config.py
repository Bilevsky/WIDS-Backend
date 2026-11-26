from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    rate_limit_per_minute: int = 120

settings = Settings()
