from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings (local-first). Defaults bind to loopback only."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SCOUT API"
    app_version: str = "0.1.0-foundation-v1.1"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000

    database_url: str = ""
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    # Ollama (abstração/configuração; verificação sob demanda, sem inferência automática)
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"
    ollama_timeout_seconds: int = 5

    # Scheduler (conservador; estado canônico no banco; desabilitado na Foundation A)
    scheduler_enabled: bool = False
    scheduler_max_concurrent_jobs: int = 1

    @property
    def backend_dir(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def data_dir(self) -> Path:
        return self.backend_dir / "data"

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def documents_dir(self) -> Path:
        return self.data_dir / "documents"

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        db_path = self.data_dir / "scout.db"
        return f"sqlite:///{db_path}"

    def ensure_storage_dirs(self) -> None:
        """Ensure local storage directories exist (DB parent, raw, documents)."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
