from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional


@dataclass
class ConnectorTestResult:
    ok: bool
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorRecord:
    """Normalized unit yielded by a connector before pipeline persistence."""

    external_id: Optional[str]
    payload: Any
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """Standard connector interface.

    New connectors must be addable without modifying core orchestration/pipeline code.
    """

    key: str
    name: str

    @abstractmethod
    def validate_config(self, config: Mapping[str, Any]) -> None:
        """Validate source-specific configuration."""

    @abstractmethod
    def check_availability(self, config: Mapping[str, Any]) -> bool:
        """Return True when the source/resource is reachable."""

    @abstractmethod
    def test_connection(self, config: Mapping[str, Any]) -> ConnectorTestResult:
        """Perform a lightweight real test query (no simulation)."""

    @abstractmethod
    def collect(self, config: Mapping[str, Any]) -> Iterable[ConnectorRecord]:
        """Fetch records (may paginate/stream)."""

    def normalize_metadata(self, raw: Mapping[str, Any]) -> Dict[str, Any]:
        """Optional initial metadata normalization hook."""
        return dict(raw)

    def describe_capabilities(self) -> Dict[str, Any]:
        return {"availability": True, "query": True, "download": False, "pagination": False}
