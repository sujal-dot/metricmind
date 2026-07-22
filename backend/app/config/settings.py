from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "postgresql://metricmind:metricmind@localhost:5433/metricmind"
    openai_api_key: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    cube_api_url: str = "http://localhost:4000/cubejs-api/v1"
    cube_api_token: str = ""
    llm_provider: Literal["groq", "openai", "gemini"] = "groq"
    groq_model: str = "llama3-8b-8192"
    openai_model: str = "gpt-4o"
    gemini_model: str = "gemini-1.5-pro"

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = False


settings = Settings()
