from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LLMAvailability:
    available: bool
    provider: str
    model: Optional[str] = None
    detail: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstraction for local/replaceable model providers (no automatic inference)."""

    provider_name: str

    @abstractmethod
    def check_availability(self) -> LLMAvailability:
        """On-demand availability/configuration check."""

    # Generation interfaces are defined here but not invoked automatically in Foundation.
    # def generate(self, prompt: str, **kwargs): ...
