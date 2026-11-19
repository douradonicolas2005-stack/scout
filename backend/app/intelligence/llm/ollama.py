from __future__ import annotations

from typing import Any, Dict

import httpx

from app.core.config import settings
from app.intelligence.llm.base import LLMAvailability, LLMProvider


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout_seconds

    def check_availability(self) -> LLMAvailability:
        """Best-effort on-demand check against local Ollama (no model execution)."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/api/tags")
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                is_json = content_type.startswith("application/json")
                data: Dict[str, Any] = resp.json() if is_json else {}
                models = [m.get("name") for m in data.get("models", []) if isinstance(m, dict)]
                has_model = self.model in models if models else None
                detail = "Ollama acessível."
                if has_model:
                    detail += " Modelo de referência encontrado."
                else:
                    detail += " Modelo de referência não confirmado."
                return LLMAvailability(
                    available=True,
                    provider=self.provider_name,
                    model=self.model,
                    detail=detail,
                    metadata={"models": models[:20]},
                )
            return LLMAvailability(
                available=False,
                provider=self.provider_name,
                model=self.model,
                detail=f"HTTP {resp.status_code}",
            )
        except Exception as exc:  # noqa: BLE001
            return LLMAvailability(
                available=False,
                provider=self.provider_name,
                model=self.model,
                detail=f"indisponível: {exc.__class__.__name__}",
            )
