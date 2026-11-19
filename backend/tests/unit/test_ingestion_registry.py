from __future__ import annotations

from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.ingestion.connectors.rss_atom import parse_feed
from app.knowledge.models.domain import AuditEvent, ProcessingEvent
from app.main import app

# Decisão 4 (confirmada pelo usuário): recurso público RSS/Atom de referência autorizado
# para teste/leitura real local (somente metadados/títulos, máx. 5 itens, read-only).
# Limites conservadores: https://www.w3.org/news/feed/
W3C_NEWS_FEED_URL = "https://www.w3.org/news/feed/"


SAMPLE_RSS = (
    b"<?xml version='1.0'?>"
    b"<rss version='2.0'><channel><title>Sample Feed</title>"
    b"<item><title>One</title><link>https://example.com/1</link>"
    b"<guid>g1</guid><pubDate>Tue, 17 Nov 2026 12:20:00 +0000</pubDate></item>"
    b"<item><title>Two</title><link>https://example.com/2</link></item>"
    b"</channel></rss>"
)


def _upgrade_tmp_db(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "ingestion_test.db"
    db_url = f"sqlite:///{db_path}"
    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "app/db/migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def _client_with_db(SessionLocal: sessionmaker[Session]) -> TestClient:
    def override_get_db() -> Iterator[Session]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_parse_feed_rss_metadata_only() -> None:
    feed_type, title, items = parse_feed(SAMPLE_RSS, max_items=5)
    assert feed_type == "rss"
    assert title == "Sample Feed"
    assert len(items) == 2
    assert items[0].title == "One"
    assert items[0].link == "https://example.com/1"
    assert items[0].item_id == "g1"
    assert items[0].published is not None


def test_connectors_list_and_get(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        resp = client.get("/api/v1/ingestion/connectors")
        assert resp.status_code == 200
        items = resp.json()["items"]
        keys = {i["key"] for i in items}
        assert "rss_atom" in keys
        rss = next(i for i in items if i["key"] == "rss_atom")
        assert rss["status"] == "registered"
        assert rss["capabilities"]["max_items_hard_limit"] == 5

        resp_one = client.get("/api/v1/ingestion/connectors/rss_atom")
        assert resp_one.status_code == 200
        assert resp_one.json()["key"] == "rss_atom"
    finally:
        app.dependency_overrides.clear()


def test_source_crud_and_activation(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        create_payload = {
            "name": "W3C News",
            "category": "institutional",
            "description": "Public news feed (metadata/titles only)",
            "resource_locator": W3C_NEWS_FEED_URL,
            "connection_type": "rss_atom",
            "status": "inactive",
            "is_active": False,
            "config_json": {"url": W3C_NEWS_FEED_URL, "max_items": 5},
            "terms_conditions": "Public feed; read-only test (metadata/titles, max 5).",
        }
        created = client.post("/api/v1/ingestion/sources", json=create_payload)
        assert created.status_code == 201
        body = created.json()
        source_id = body["id"]
        assert body["name"] == "W3C News"
        assert body["connection_type"] == "rss_atom"
        assert body["is_active"] is False

        listing = client.get("/api/v1/ingestion/sources")
        assert listing.status_code == 200
        assert any(s["id"] == source_id for s in listing.json()["items"])

        detail = client.get(f"/api/v1/ingestion/sources/{source_id}")
        assert detail.status_code == 200

        updated = client.patch(
            f"/api/v1/ingestion/sources/{source_id}",
            json={"is_active": True, "status": "active", "frequency": "manual"},
        )
        assert updated.status_code == 200
        ubody = updated.json()
        assert ubody["is_active"] is True
        assert ubody["status"] == "active"
        assert ubody["frequency"] == "manual"

        active_only = client.get("/api/v1/ingestion/sources", params={"active_only": "true"})
        assert active_only.status_code == 200
        assert any(s["id"] == source_id for s in active_only.json()["items"])

        with SessionLocal() as db:
            audits = db.execute(
                select(AuditEvent).where(AuditEvent.target_id == source_id)
            ).scalars().all()
            actions = {a.action for a in audits}
            assert "source.create" in actions
            assert "source.update" in actions
    finally:
        app.dependency_overrides.clear()


def test_source_validation_rejects_unknown_connector(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        resp = client.post(
            "/api/v1/ingestion/sources",
            json={
                "name": "Bad",
                "resource_locator": "https://example.com",
                "connection_type": "unknown_connector",
            },
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_source_test_connection_real_feed(tmp_path: Path) -> None:
    """Real read-only test against public W3C news feed (metadata/titles, max 5)."""
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        created = client.post(
            "/api/v1/ingestion/sources",
            json={
                "name": "W3C News (real test)",
                "resource_locator": W3C_NEWS_FEED_URL,
                "connection_type": "rss_atom",
                "config_json": {"url": W3C_NEWS_FEED_URL, "max_items": 5, "timeout_seconds": 10},
                "terms_conditions": "Public W3C feed; authorized read-only local test.",
            },
        )
        assert created.status_code == 201
        source_id = created.json()["id"]

        resp = client.post(f"/api/v1/ingestion/sources/{source_id}/test-connection")
        assert resp.status_code == 200
        body = resp.json()
        assert body["source_id"] == source_id
        assert body["connector_key"] == "rss_atom"
        assert body["ok"] is True
        assert body["metadata"]["items_returned"] <= 5
        assert len(body["metadata"].get("items", [])) <= 5
        # metadata/titles only (no full content/body fields)
        if body["metadata"].get("items"):
            first = body["metadata"]["items"][0]
            assert "title" in first
            assert "content" not in first
            assert "description" not in first

        with SessionLocal() as db:
            events = db.execute(
                select(ProcessingEvent).where(ProcessingEvent.stage == "connection_test")
            ).scalars().all()
            assert len(events) >= 1
            assert any(e.status == "succeeded" for e in events)
            audits = db.execute(
                select(AuditEvent).where(
                    AuditEvent.target_id == source_id,
                    AuditEvent.action == "source.test_connection",
                )
            ).scalars().all()
            assert len(audits) >= 1
    finally:
        app.dependency_overrides.clear()
