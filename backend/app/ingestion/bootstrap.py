from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.connectors.rss_atom import RssAtomConnector
from app.ingestion.registry import (
    get_connector_class,
    list_connector_keys,
    register_connector,
)
from app.knowledge.models.domain import Connector

BUILTIN_CONNECTORS = [RssAtomConnector]


def ensure_builtin_connectors_registered() -> None:
    for cls in BUILTIN_CONNECTORS:
        if get_connector_class(cls.key) is None:
            register_connector(cls)


def _rss_atom_config_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri"},
            "max_items": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "default": 5,
            },
            "timeout_seconds": {
                "type": "number",
                "minimum": 1,
                "maximum": 30,
                "default": 10,
            },
        },
        "required": ["url"],
    }


def sync_builtin_connectors_to_db(db: Session) -> None:
    """Upsert built-in connector metadata rows (idempotent)."""
    ensure_builtin_connectors_registered()
    for key in list_connector_keys():
        cls = get_connector_class(key)
        if cls is None:
            continue
        instance = cls()
        existing = db.execute(
            select(Connector).where(Connector.key == key)
        ).scalar_one_or_none()
        capabilities = instance.describe_capabilities()
        config_schema = _rss_atom_config_schema() if key == "rss_atom" else None
        if existing is None:
            db.add(
                Connector(
                    key=key,
                    name=getattr(cls, "name", key),
                    version="1.0.0",
                    capabilities_json=capabilities,
                    config_schema_json=config_schema,
                    status="registered",
                )
            )
        else:
            existing.name = getattr(cls, "name", existing.name)
            existing.version = existing.version or "1.0.0"
            existing.capabilities_json = capabilities
            if existing.config_schema_json is None and config_schema is not None:
                existing.config_schema_json = config_schema
            existing.status = "registered"
    db.commit()
