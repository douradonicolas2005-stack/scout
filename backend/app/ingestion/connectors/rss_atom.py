from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional
from urllib.parse import urlparse

import httpx

from app.ingestion.connectors.base import (
    BaseConnector,
    ConnectorRecord,
    ConnectorTestResult,
)

MAX_ITEMS_HARD_LIMIT = 5
DEFAULT_MAX_ITEMS = 5
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_RESPONSE_BYTES = 512_000


@dataclass
class FeedItem:
    title: Optional[str]
    link: Optional[str]
    published: Optional[str]
    item_id: Optional[str]

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "link": self.link,
            "published": self.published,
            "id": self.item_id,
        }


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _text(elem: Optional[ET.Element]) -> Optional[str]:
    if elem is None or elem.text is None:
        return None
    value = elem.text.strip()
    return value or None


def _parse_datetime(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            return dt.isoformat()
        return dt.astimezone().isoformat()
    except Exception:  # noqa: BLE001
        pass
    try:
        # Atom ISO-ish
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.isoformat()
    except Exception:  # noqa: BLE001
        return value.strip() or None


def _find_child(elem: ET.Element, name: str) -> Optional[ET.Element]:
    for child in list(elem):
        if _strip_ns(child.tag).lower() == name.lower():
            return child
    return None


def _find_children(elem: ET.Element, name: str) -> List[ET.Element]:
    out: List[ET.Element] = []
    for child in list(elem):
        if _strip_ns(child.tag).lower() == name.lower():
            out.append(child)
    return out


def parse_feed(xml_bytes: bytes, max_items: int) -> tuple[str, str, List[FeedItem]]:
    """Parse RSS 2.0 or Atom feed and return (feed_type, feed_title, items)."""
    if len(xml_bytes) > MAX_RESPONSE_BYTES:
        raise ValueError("Feed response exceeds size limit")

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML feed: {exc}") from exc

    root_name = _strip_ns(root.tag).lower()
    items: List[FeedItem] = []

    if root_name == "rss":
        channel = _find_child(root, "channel")
        if channel is None:
            raise ValueError("RSS feed missing channel element")
        feed_title = _text(_find_child(channel, "title")) or ""
        for item in _find_children(channel, "item")[:max_items]:
            link = _text(_find_child(item, "link"))
            if not link:
                # try guid as permalink-like fallback not assumed; keep link None
                link = None
            items.append(
                FeedItem(
                    title=_text(_find_child(item, "title")),
                    link=link,
                    published=_parse_datetime(_text(_find_child(item, "pubDate"))),
                    item_id=_text(_find_child(item, "guid")),
                )
            )
        return "rss", feed_title, items

    if root_name == "feed":
        feed_title = _text(_find_child(root, "title")) or ""
        for entry in _find_children(root, "entry")[:max_items]:
            entry_link: Optional[str] = None
            for link_el in _find_children(entry, "link"):
                href = (link_el.attrib.get("href") or "").strip()
                if href:
                    rel = (link_el.attrib.get("rel") or "alternate").lower()
                    if rel in {"alternate", "", "self"}:
                        entry_link = href
                        break
                    if entry_link is None:
                        entry_link = href
            published = _text(_find_child(entry, "published")) or _text(
                _find_child(entry, "updated")
            )
            items.append(
                FeedItem(
                    title=_text(_find_child(entry, "title")),
                    link=entry_link,
                    published=_parse_datetime(published),
                    item_id=_text(_find_child(entry, "id")),
                )
            )
        return "atom", feed_title, items

    raise ValueError(f"Unsupported feed root element: {root_name}")


class RssAtomConnector(BaseConnector):
    """Read-only RSS/Atom connector (Foundation E: test/minimal fetch, metadata only)."""

    key = "rss_atom"
    name = "RSS/Atom Feed"

    def validate_config(self, config: Mapping[str, Any]) -> None:
        url = str(config.get("url") or "").strip()
        if not url:
            raise ValueError("url is required")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("url must use http or https")
        if not parsed.netloc:
            raise ValueError("url must include a network location")
        max_items = config.get("max_items", DEFAULT_MAX_ITEMS)
        try:
            max_items_int = int(max_items)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("max_items must be an integer") from exc
        if max_items_int < 1:
            raise ValueError("max_items must be >= 1")
        timeout = config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
        try:
            timeout_f = float(timeout)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("timeout_seconds must be a number") from exc
        if timeout_f <= 0 or timeout_f > 30:
            raise ValueError("timeout_seconds must be > 0 and <= 30")

    def _effective_config(self, config: Mapping[str, Any]) -> Dict[str, Any]:
        self.validate_config(config)
        max_items = int(config.get("max_items", DEFAULT_MAX_ITEMS))
        # Safety/restriction: cap items to hard limit (metadata/titles only)
        max_items = min(max_items, MAX_ITEMS_HARD_LIMIT)
        timeout = float(config.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
        return {
            "url": str(config["url"]).strip(),
            "max_items": max_items,
            "timeout_seconds": timeout,
        }

    def _fetch(self, url: str, timeout_seconds: float) -> bytes:
        headers = {
            "User-Agent": "SCOUT-Foundation/1.0 (local-readonly-test)",
            "Accept": (
                "application/rss+xml, application/atom+xml, application/xml, "
                "text/xml, */*;q=0.1"
            ),
        }
        with httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
            headers=headers,
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            content = resp.content
            if len(content) > MAX_RESPONSE_BYTES:
                raise ValueError("Feed response exceeds size limit")
            return content

    def check_availability(self, config: Mapping[str, Any]) -> bool:
        try:
            result = self.test_connection(config)
            return result.ok
        except Exception:  # noqa: BLE001
            return False

    def test_connection(self, config: Mapping[str, Any]) -> ConnectorTestResult:
        try:
            cfg = self._effective_config(config)
            content = self._fetch(cfg["url"], cfg["timeout_seconds"])
            feed_type, feed_title, items = parse_feed(content, cfg["max_items"])
            sample = [it.to_metadata() for it in items]
            return ConnectorTestResult(
                ok=True,
                message="Feed fetched and parsed successfully",
                metadata={
                    "url": cfg["url"],
                    "feed_type": feed_type,
                    "feed_title": feed_title,
                    "items_returned": len(items),
                    "max_items": cfg["max_items"],
                    "items": sample,
                },
            )
        except httpx.HTTPStatusError as exc:
            return ConnectorTestResult(
                ok=False,
                message=f"HTTP error: {exc.response.status_code}",
                metadata={"url": str(config.get("url") or "")},
            )
        except Exception as exc:  # noqa: BLE001
            return ConnectorTestResult(
                ok=False,
                message=f"{exc.__class__.__name__}: {exc}",
                metadata={"url": str(config.get("url") or "")},
            )

    def collect(self, config: Mapping[str, Any]) -> Iterable[ConnectorRecord]:
        """Minimal read-only fetch yielding metadata records (no pipeline persistence in E)."""
        cfg = self._effective_config(config)
        content = self._fetch(cfg["url"], cfg["timeout_seconds"])
        feed_type, feed_title, items = parse_feed(content, cfg["max_items"])
        for idx, item in enumerate(items):
            meta = item.to_metadata()
            meta.update({"feed_type": feed_type, "feed_title": feed_title, "url": cfg["url"]})
            yield ConnectorRecord(
                external_id=item.item_id or item.link or f"item-{idx}",
                payload={"title": item.title},
                metadata=meta,
            )

    def describe_capabilities(self) -> Dict[str, Any]:
        return {
            "availability": True,
            "query": True,
            "download": False,
            "pagination": False,
            "formats": ["rss", "atom"],
            "metadata_only": True,
            "max_items_hard_limit": MAX_ITEMS_HARD_LIMIT,
        }
