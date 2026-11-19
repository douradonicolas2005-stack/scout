from __future__ import annotations

from app.core.config import settings


def test_defaults_bind_loopback() -> None:
    assert settings.host == "127.0.0.1"
    assert "127.0.0.1" in settings.cors_origins or "localhost" in settings.cors_origins


def test_ollama_defaults_local() -> None:
    assert settings.ollama_base_url.startswith("http://127.0.0.1")
    assert settings.ollama_model == "qwen3:4b"


def test_scheduler_disabled_by_default() -> None:
    assert settings.scheduler_enabled is False
    assert settings.scheduler_max_concurrent_jobs == 1


def test_storage_paths_defined() -> None:
    assert settings.data_dir.name == "data"
    assert settings.raw_data_dir.name == "raw"
    assert settings.documents_dir.name == "documents"
