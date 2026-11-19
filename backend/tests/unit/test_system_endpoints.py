from __future__ import annotations

from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.main import app


def _upgrade_tmp_db(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "api_test.db"
    db_url = f"sqlite:///{db_path}"
    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "app/db/migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def test_system_info_returns_modules_and_metadata(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)

    def override_get_db() -> Iterator[Session]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        resp = client.get("/api/v1/system/info")
        assert resp.status_code == 200
        body = resp.json()
        assert body["phase"] == "foundation-g"
        assert body["api_version"] == "v1"
        assert body["database"] == "sqlite"
        assert body["ollama"]["mode"] == "abstraction-availability-only"
        assert isinstance(body["modules"], list)
        assert len(body["modules"]) == 8
        keys = {m["key"] for m in body["modules"]}
        expected_keys = {
            "radar",
            "dossiers",
            "knowledge-graph",
            "predictions",
            "scenario-lab",
            "action-center",
            "agent-control",
            "system",
        }
        assert keys == expected_keys
        assert all(
            m["status"] == "placeholder" and m["implemented"] is False
            for m in body["modules"]
        )
    finally:
        app.dependency_overrides.clear()


def test_db_status_reports_migrated_schema(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)

    def override_get_db() -> Iterator[Session]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        resp = client.get("/api/v1/db/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["connected"] is True
        assert body["dialect"] == "sqlite"
        assert body["table_count"] >= 15
        table_names = {t["name"] for t in body["tables"]}
        expected = {
            "sources",
            "connectors",
            "collection_jobs",
            "collection_runs",
            "raw_records",
            "documents",
            "extracted_claims",
            "evidence",
            "entities",
            "relationships",
            "data_changes",
            "processing_events",
            "agent_runs",
            "audit_events",
        }
        assert expected.issubset(table_names)
        assert "alembic_version" in table_names
        assert body["alembic_revision"] is not None
        assert isinstance(body["alembic_revisions"], list) and len(body["alembic_revisions"]) >= 1
        assert body["error"] is None
    finally:
        app.dependency_overrides.clear()
