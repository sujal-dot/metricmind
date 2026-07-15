from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "postgresql://metricmind:metricmind@localhost:5432/metricmind"
    openai_api_key: str = ""
    groq_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

