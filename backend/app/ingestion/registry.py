"""Source/connector registry (in-memory connector classes + helpers)."""

from __future__ import annotations

from typing import Dict, Type

from app.ingestion.connectors.base import BaseConnector

_CONNECTORS: Dict[str, Type[BaseConnector]] = {}


def register_connector(connector_cls: Type[BaseConnector]) -> None:
    _CONNECTORS[connector_cls.key] = connector_cls


def get_connector_class(key: str) -> Type[BaseConnector] | None:
    return _CONNECTORS.get(key)


def list_connector_keys() -> list[str]:
    return sorted(_CONNECTORS.keys())
