from __future__ import annotations

from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import get_db
from app.ingestion.collection import create_collection_job, execute_collection_job
from app.ingestion.scheduler import IngestionScheduler
from app.knowledge.models.domain import (
    CollectionJob,
    CollectionRun,
    DataChange,
    ProcessingEvent,
    RawRecord,
)
from app.main import app

# Decisão 4 (auto-aplicada, pendente de confirmação explícita): recurso público real para
# teste/leitura local (somente metadados/títulos, máx. 5 itens, read-only).
W3C_NEWS_FEED_URL = "https://www.w3.org/news/feed/"


def _upgrade_tmp_db(tmp_path: Path) -> sessionmaker[Session]:
    db_path = tmp_path / "pipeline_test.db"
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


def _create_source(client: TestClient) -> str:
    created = client.post(
        "/api/v1/ingestion/sources",
        json={
            "name": "W3C News Pipeline",
            "resource_locator": W3C_NEWS_FEED_URL,
            "connection_type": "rss_atom",
            "status": "active",
            "is_active": True,
            "config_json": {"url": W3C_NEWS_FEED_URL, "max_items": 5, "timeout_seconds": 10},
            "terms_conditions": "Public W3C feed; authorized read-only local test.",
            "permissions_json": {"allow_storage": False},
        },
    )
    assert created.status_code == 201
    return created.json()["id"]


def test_create_and_run_collection_job_real_pipeline(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        source_id = _create_source(client)

        resp = client.post(
            "/api/v1/ingestion/jobs",
            json={
                "source_id": source_id,
                "trigger": "manual",
                "execute_now": True,
                "max_attempts": 2,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["job"]["source_id"] == source_id
        assert body["job"]["status"] in {"succeeded", "failed", "pending"}
        assert body["run"] is not None
        run = body["run"]
        assert run["source_id"] == source_id
        assert run["status"] == "succeeded"
        assert run["items_found"] <= 5
        assert run["items_stored"] >= 0
        assert run["items_deduplicated"] == 0

        job_id = body["job"]["id"]
        run_id = run["id"]

        job_resp = client.get(f"/api/v1/ingestion/jobs/{job_id}")
        assert job_resp.status_code == 200
        assert job_resp.json()["status"] == "succeeded"

        runs_resp = client.get(f"/api/v1/ingestion/jobs/{job_id}/runs")
        assert runs_resp.status_code == 200
        assert len(runs_resp.json()["items"]) == 1

        events_resp = client.get(f"/api/v1/ingestion/runs/{run_id}/events")
        assert events_resp.status_code == 200
        stages = {e["stage"] for e in events_resp.json()["items"]}
        assert {"job", "run", "identify", "collect", "normalize_validate_dedupe_store"} & stages

        with SessionLocal() as db:
            raws = db.execute(select(RawRecord).where(RawRecord.run_id == run_id)).scalars().all()
            assert len(raws) == run["items_stored"]
            assert all(r.is_preserved is False for r in raws)
            assert all((r.metadata_json or {}).get("title") or r.external_id for r in raws)

            changes = db.execute(
                select(DataChange).where(DataChange.run_id == run_id)
            ).scalars().all()
            assert len(changes) == run["items_stored"]

            events = db.execute(
                select(ProcessingEvent).where(ProcessingEvent.run_id == run_id)
            ).scalars().all()
            assert any(e.status == "succeeded" and e.stage == "run" for e in events)
    finally:
        app.dependency_overrides.clear()


def test_pipeline_deduplicates_on_second_run(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        source_id = _create_source(client)

        first = client.post(
            "/api/v1/ingestion/jobs",
            json={"source_id": source_id, "trigger": "manual", "execute_now": True},
        )
        assert first.status_code == 201
        first_run = first.json()["run"]
        assert first_run["status"] == "succeeded"
        stored_first = first_run["items_stored"]

        second = client.post(
            "/api/v1/ingestion/jobs",
            json={"source_id": source_id, "trigger": "manual", "execute_now": True},
        )
        assert second.status_code == 201
        second_run = second.json()["run"]
        assert second_run["status"] == "succeeded"
        assert second_run["items_stored"] == 0
        assert second_run["items_deduplicated"] == stored_first

        with SessionLocal() as db:
            raws = (
                db.execute(select(RawRecord).where(RawRecord.source_id == source_id))
                .scalars()
                .all()
            )
            assert len(raws) == stored_first
            runs = (
                db.execute(select(CollectionRun).where(CollectionRun.source_id == source_id))
                .scalars()
                .all()
            )
            assert len(runs) == 2
    finally:
        app.dependency_overrides.clear()


def test_job_not_executed_when_execute_now_false(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    client = _client_with_db(SessionLocal)
    try:
        source_id = _create_source(client)
        resp = client.post(
            "/api/v1/ingestion/jobs",
            json={"source_id": source_id, "trigger": "manual", "execute_now": False},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["run"] is None
        assert body["job"]["status"] == "pending"

        with SessionLocal() as db:
            job = db.get(CollectionJob, body["job"]["id"])
            assert job is not None
            assert job.status == "pending"
    finally:
        app.dependency_overrides.clear()


def test_scheduler_dispatches_pending_job_from_db(tmp_path: Path) -> None:
    SessionLocal = _upgrade_tmp_db(tmp_path)
    with SessionLocal() as db:
        from app.knowledge.models.domain import Source

        source = Source(
            name="W3C News Scheduler",
            resource_locator=W3C_NEWS_FEED_URL,
            connection_type="rss_atom",
            status="active",
            is_active=True,
            config_json={"url": W3C_NEWS_FEED_URL, "max_items": 5, "timeout_seconds": 10},
            terms_conditions="Public W3C feed; authorized read-only local test.",
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        job = create_collection_job(
            db, source_id=source.id, trigger="manual", requested_by="test"
        )
        job_id = job.id

    def _exec(jid: str) -> None:
        db = SessionLocal()
        try:
            execute_collection_job(db, jid)
        finally:
            db.close()

    scheduler = IngestionScheduler(
        enabled=True,
        max_concurrent_jobs=1,
        session_factory=SessionLocal,
        poll_seconds=5,
        executor=_exec,
    )
    # dispatch_once is the controlled DB-canonical execution tick
    scheduler._dispatch_once()

    with SessionLocal() as db:
        job = db.get(CollectionJob, job_id)
        assert job is not None
        assert job.status == "succeeded"
        runs = (
            db.execute(select(CollectionRun).where(CollectionRun.job_id == job_id))
            .scalars()
            .all()
        )
        assert len(runs) == 1
        assert runs[0].status == "succeeded"
        raws = (
            db.execute(select(RawRecord).where(RawRecord.source_id == job.source_id))
            .scalars()
            .all()
        )
        assert len(raws) == runs[0].items_stored
