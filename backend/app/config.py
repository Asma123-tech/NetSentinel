# app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://netsentinel:netsentinel@db:5432/netsentinel"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    SEARCH_PROVIDER: str = "searxng"

    SEARXNG_URL: str = "http://searxng:8080"

    SEARXNG_CATEGORIES: str = "general,images"

    JWT_SECRET_KEY: str = "netsentinel-secret-key-12345-fyp-project"

    class Config:
        env_file = ".env"


settings = Settings()