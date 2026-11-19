"""Connector implementations and registry hooks (plugável)."""

from app.ingestion.connectors.rss_atom import RssAtomConnector

__all__ = ["RssAtomConnector"]
