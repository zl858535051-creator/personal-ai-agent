from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Personal AI Agent"
    backend_dir: Path = Path(__file__).resolve().parents[2]
    database_url: str = "sqlite:///./storage/app.db"

    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    embedding_dim: int = 384
    chunk_size: int = 900
    chunk_overlap: int = 120
    retrieval_top_k: int = 5

    upload_dir: Path = Path("storage/uploads")
    report_dir: Path = Path("storage/reports")
    vector_dir: Path = Path("storage/vector_db")

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @property
    def absolute_upload_dir(self) -> Path:
        return (self.backend_dir / self.upload_dir).resolve()

    @property
    def absolute_report_dir(self) -> Path:
        return (self.backend_dir / self.report_dir).resolve()

    @property
    def absolute_vector_dir(self) -> Path:
        return (self.backend_dir / self.vector_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.absolute_upload_dir.mkdir(parents=True, exist_ok=True)
    settings.absolute_report_dir.mkdir(parents=True, exist_ok=True)
    settings.absolute_vector_dir.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()

