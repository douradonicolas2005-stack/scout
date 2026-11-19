from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.knowledge.models.domain import (
    CollectionJob,
    CollectionRun,
    ExtractedClaim,
    RawRecord,
    Source,
)
from app.knowledge.provenance import ClaimType, VerificationStatus

EXPECTED_TABLES = {
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


def _make_engine(tmp_path: Path) -> tuple[Engine, sessionmaker[Session]]:
    db_path = tmp_path / "scout_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    # apply pragmas similar to runtime
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA busy_timeout=5000"))

    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    return engine, SessionLocal


def _alembic_upgrade_head(tmp_path: Path) -> None:
    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "app/db/migrations"))
    db_path = tmp_path / "scout_test.db"
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    command.upgrade(cfg, "head")


def test_alembic_migration_creates_all_tables(tmp_path: Path) -> None:
    _alembic_upgrade_head(tmp_path)
    engine, _ = _make_engine(tmp_path)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(tables)
    assert "alembic_version" in tables
    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert isinstance(rev, str) and rev


def test_basic_read_write_and_provenance(tmp_path: Path) -> None:
    _alembic_upgrade_head(tmp_path)
    _, SessionLocal = _make_engine(tmp_path)

    with SessionLocal() as db:
        source = Source(
            name="Test Source",
            resource_locator="https://example.com/feed",
            connection_type="http_generic",
        )
        db.add(source)
        db.flush()

        job = CollectionJob(source_id=source.id, trigger="manual", status="pending")
        db.add(job)
        db.flush()

        run = CollectionRun(
            job_id=job.id,
            source_id=source.id,
            run_number=1,
            status="running",
        )
        db.add(run)
        db.flush()

        raw = RawRecord(
            source_id=source.id,
            run_id=run.id,
            external_id="ext-1",
            content_hash="hash-1",
        )
        db.add(raw)
        db.flush()

        claim = ExtractedClaim(
            source_id=source.id,
            raw_record_id=raw.id,
            claim_text="Declaracao inicial",
            claim_type=ClaimType.DECLARACAO.value,
            verification_status=VerificationStatus.NAO_VERIFICADO.value,
            confidence=0.4,
            version=1,
        )
        db.add(claim)
        db.commit()

        stored_claim = db.query(ExtractedClaim).one()
        assert stored_claim.claim_type == ClaimType.DECLARACAO.value
        assert stored_claim.claim_type != ClaimType.FATO_VERIFICADO.value
        assert stored_claim.verification_status == VerificationStatus.NAO_VERIFICADO.value
        assert stored_claim.version == 1
        assert stored_claim.source_id == source.id
        assert stored_claim.raw_record_id == raw.id
