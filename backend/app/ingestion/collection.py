from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion.bootstrap import ensure_builtin_connectors_registered
from app.ingestion.connectors.base import BaseConnector, ConnectorRecord
from app.ingestion.registry import get_connector_class
from app.knowledge.models.domain import (
    AuditEvent,
    CollectionJob,
    CollectionRun,
    DataChange,
    ProcessingEvent,
    RawRecord,
    Source,
)

logger = logging.getLogger(__name__)


class CollectionError(Exception):
    """Raised for controlled collection/pipeline failures."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _record_event(
    db: Session,
    *,
    stage: str,
    status: str,
    message: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> ProcessingEvent:
    event = ProcessingEvent(
        job_id=job_id,
        run_id=run_id,
        stage=stage,
        status=status,
        message=message,
        payload_json=payload or {},
    )
    db.add(event)
    return event


def _record_data_change(
    db: Session,
    *,
    entity_table: str,
    entity_id: str,
    change_type: str,
    after: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    run_id: Optional[str] = None,
    actor: str = "system:pipeline",
) -> None:
    db.add(
        DataChange(
            entity_table=entity_table,
            entity_id=entity_id,
            change_type=change_type,
            before_json=None,
            after_json=after,
            reason=reason,
            run_id=run_id,
            actor=actor,
        )
    )


def _record_audit(
    db: Session,
    *,
    action: str,
    target_type: Optional[str],
    target_id: Optional[str],
    severity: str = "info",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    db.add(
        AuditEvent(
            actor_type="system",
            actor_id="pipeline",
            action=action,
            target_type=target_type,
            target_id=target_id,
            severity=severity,
            details_json=details or {},
            ip_or_origin="127.0.0.1",
        )
    )


def _source_connector_and_config(source: Source) -> Tuple[BaseConnector, Dict[str, Any]]:
    ensure_builtin_connectors_registered()
    cls = get_connector_class(source.connection_type)
    if cls is None:
        raise CollectionError(f"Unknown connector: {source.connection_type}")
    connector = cls()
    cfg = dict(source.config_json or {})
    if "url" not in cfg and source.resource_locator:
        cfg["url"] = source.resource_locator
    connector.validate_config(cfg)
    return connector, cfg


def _should_preserve_raw(source: Source) -> bool:
    cfg = dict(source.config_json or {})
    perms = dict(source.permissions_json or {})
    if bool(cfg.get("preserve_raw")):
        return True
    if bool(perms.get("preserve_raw")):
        return True
    if bool(perms.get("allow_storage")):
        return True
    return False


def _content_hash(record: ConnectorRecord) -> str:
    base = {
        "external_id": record.external_id,
        "payload": record.payload,
        "metadata": record.metadata,
    }
    raw = json.dumps(base, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _next_run_number(db: Session, job_id: str) -> int:
    rows = db.execute(
        select(CollectionRun.run_number).where(CollectionRun.job_id == job_id)
    ).scalars().all()
    return (max(rows) if rows else 0) + 1


def create_collection_job(
    db: Session,
    *,
    source_id: str,
    trigger: str = "manual",
    requested_by: Optional[str] = None,
    scheduled_for: Optional[datetime] = None,
    max_attempts: int = 3,
) -> CollectionJob:
    source = db.get(Source, source_id)
    if source is None:
        raise CollectionError("Source not found")
    if not source.is_active and trigger != "manual":
        raise CollectionError("Source is not active")
    job = CollectionJob(
        source_id=source_id,
        trigger=trigger,
        status="pending",
        priority=0,
        scheduled_for=scheduled_for,
        attempt=0,
        max_attempts=max(1, min(max_attempts, 5)),
        requested_by=requested_by,
    )
    db.add(job)
    db.flush()
    _record_audit(
        db,
        action="collection_job.create",
        target_type="collection_job",
        target_id=job.id,
        details={"source_id": source_id, "trigger": trigger},
    )
    _record_event(
        db,
        stage="job",
        status="created",
        message="Collection job created",
        payload={"source_id": source_id, "trigger": trigger},
        job_id=job.id,
    )
    db.commit()
    db.refresh(job)
    return job


def _find_existing_raw(
    db: Session, *, source_id: str, external_id: Optional[str], content_hash: str
) -> Optional[RawRecord]:
    if external_id:
        existing = db.execute(
            select(RawRecord).where(
                RawRecord.source_id == source_id,
                RawRecord.external_id == external_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
    return db.execute(
        select(RawRecord).where(
            RawRecord.source_id == source_id,
            RawRecord.content_hash == content_hash,
        )
    ).scalar_one_or_none()


def _persist_raw_record(
    db: Session,
    *,
    source: Source,
    run: CollectionRun,
    record: ConnectorRecord,
    content_hash: str,
    preserve_raw: bool,
) -> RawRecord:
    storage_path: Optional[str] = None
    is_preserved = False
    metadata = dict(record.metadata or {})
    metadata.setdefault("payload", record.payload)
    metadata.setdefault("ingested_via", "pipeline_f")

    raw = RawRecord(
        source_id=source.id,
        run_id=run.id,
        external_id=record.external_id,
        content_hash=content_hash,
        content_type="application/json",
        storage_path=None,
        is_preserved=False,
        license_note=source.terms_conditions,
        metadata_json=metadata,
        source_locator=(
            str(metadata.get("link") or metadata.get("url") or source.resource_locator)
        ),
        published_at=None,
        collected_at=_utcnow(),
        occurred_at=None,
        valid_from=None,
        valid_to=None,
    )
    db.add(raw)
    db.flush()

    if preserve_raw:
        settings.ensure_storage_dirs()
        out_dir = settings.raw_data_dir / source.id
        out_dir.mkdir(parents=True, exist_ok=True)
        file_path = out_dir / f"{raw.id}.json"
        payload = {
            "raw_record_id": raw.id,
            "source_id": source.id,
            "run_id": run.id,
            "external_id": record.external_id,
            "content_hash": content_hash,
            "metadata": metadata,
            "payload": record.payload,
            "collected_at": raw.collected_at.isoformat() if raw.collected_at else None,
        }
        file_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        try:
            storage_path = str(file_path.relative_to(settings.backend_dir))
        except ValueError:
            storage_path = str(file_path)
        raw.storage_path = storage_path
        raw.is_preserved = True
        is_preserved = True

    _record_data_change(
        db,
        entity_table="raw_records",
        entity_id=raw.id,
        change_type="create",
        after={
            "source_id": source.id,
            "run_id": run.id,
            "external_id": record.external_id,
            "content_hash": content_hash,
            "is_preserved": is_preserved,
            "storage_path": storage_path,
        },
        reason="Collected and persisted by pipeline",
        run_id=run.id,
    )
    return raw


def execute_collection_job(db: Session, job_id: str) -> CollectionRun:
    """Execute a collection job synchronously (controlled, single-run)."""
    job = db.get(CollectionJob, job_id)
    if job is None:
        raise CollectionError("Collection job not found")
    source = db.get(Source, job.source_id)
    if source is None:
        raise CollectionError("Source not found for job")

    if job.status in {"succeeded", "running"}:
        # Avoid duplicate concurrent execution; caller can inspect state.
        existing_run = db.execute(
            select(CollectionRun)
            .where(CollectionRun.job_id == job.id)
            .order_by(CollectionRun.started_at.desc())
        ).scalars().first()
        if existing_run is not None:
            return existing_run
        raise CollectionError(f"Job is not executable in status '{job.status}'")

    now = _utcnow()
    job.status = "running"
    job.started_at = job.started_at or now
    job.attempt = (job.attempt or 0) + 1
    job.error_summary = None

    run = CollectionRun(
        job_id=job.id,
        source_id=source.id,
        run_number=_next_run_number(db, job.id),
        status="running",
        started_at=now,
    )
    db.add(run)
    db.flush()

    _record_event(
        db,
        stage="run",
        status="started",
        message="Collection run started",
        payload={"job_id": job.id, "run_number": run.run_number},
        job_id=job.id,
        run_id=run.id,
    )
    db.commit()

    items_found = 0
    items_stored = 0
    items_deduplicated = 0
    items_invalid = 0
    bytes_downloaded = 0

    try:
        _record_event(
            db,
            stage="identify",
            status="ok",
            message="Source and connector identified",
            payload={"source_id": source.id, "connector": source.connection_type},
            job_id=job.id,
            run_id=run.id,
        )
        connector, cfg = _source_connector_and_config(source)
        _record_event(
            db,
            stage="collect",
            status="started",
            message="Collecting records from connector",
            payload={"connector": source.connection_type},
            job_id=job.id,
            run_id=run.id,
        )
        records: List[ConnectorRecord] = list(connector.collect(cfg))
        items_found = len(records)
        bytes_downloaded = len(
            json.dumps([r.metadata for r in records], default=str).encode("utf-8")
        )
        _record_event(
            db,
            stage="collect",
            status="succeeded",
            message="Collection fetch completed",
            payload={"items_found": items_found},
            job_id=job.id,
            run_id=run.id,
        )

        preserve_raw = _should_preserve_raw(source)
        _record_event(
            db,
            stage="normalize_validate_dedupe_store",
            status="started",
            message="Normalizing, validating, deduplicating and storing records",
            payload={"preserve_raw": preserve_raw},
            job_id=job.id,
            run_id=run.id,
        )

        for rec in records:
            # basic validation
            title = (rec.metadata or {}).get("title") or (rec.payload or {}).get("title")
            link = (rec.metadata or {}).get("link")
            if not rec.external_id and not title and not link:
                items_invalid += 1
                continue

            content_hash = _content_hash(rec)
            existing = _find_existing_raw(
                db,
                source_id=source.id,
                external_id=rec.external_id,
                content_hash=content_hash,
            )
            if existing is not None:
                items_deduplicated += 1
                continue

            _persist_raw_record(
                db,
                source=source,
                run=run,
                record=rec,
                content_hash=content_hash,
                preserve_raw=preserve_raw,
            )
            items_stored += 1

        run.items_found = items_found
        run.items_stored = items_stored
        run.items_deduplicated = items_deduplicated
        run.items_invalid = items_invalid
        run.bytes_downloaded = bytes_downloaded
        run.status = "succeeded"
        run.finished_at = _utcnow()
        run.metrics_json = {
            "preserve_raw": preserve_raw,
            "connector": source.connection_type,
        }

        job.status = "succeeded"
        job.finished_at = run.finished_at
        source.last_collected_at = run.finished_at

        _record_event(
            db,
            stage="normalize_validate_dedupe_store",
            status="succeeded",
            message="Pipeline processing completed",
            payload={
                "items_found": items_found,
                "items_stored": items_stored,
                "items_deduplicated": items_deduplicated,
                "items_invalid": items_invalid,
            },
            job_id=job.id,
            run_id=run.id,
        )
        _record_event(
            db,
            stage="run",
            status="succeeded",
            message="Collection run succeeded",
            payload={"run_id": run.id},
            job_id=job.id,
            run_id=run.id,
        )
        db.commit()
        db.refresh(run)
        return run

    except Exception as exc:  # noqa: BLE001
        logger.exception("Collection job failed: %s", job_id)
        err_msg = f"{exc.__class__.__name__}: {exc}"
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            pass

        job_db = db.get(CollectionJob, job_id)
        run_db = db.get(CollectionRun, run.id)
        if job_db is None or run_db is None:
            raise

        run_db.status = "failed"
        run_db.error_message = err_msg
        run_db.finished_at = _utcnow()
        run_db.items_found = items_found
        run_db.items_stored = items_stored
        run_db.items_deduplicated = items_deduplicated
        run_db.items_invalid = items_invalid
        run_db.bytes_downloaded = bytes_downloaded

        job_db.error_summary = err_msg
        job_db.finished_at = run_db.finished_at
        # Conservative retry policy
        if job_db.attempt < job_db.max_attempts:
            job_db.status = "pending"
            job_db.scheduled_for = _utcnow()
        else:
            job_db.status = "failed"

        _record_event(
            db,
            stage="run",
            status="failed",
            message=err_msg,
            payload={"attempt": job_db.attempt, "max_attempts": job_db.max_attempts},
            job_id=job_db.id,
            run_id=run_db.id,
        )
        db.commit()
        db.refresh(run_db)
        return run_db


def get_job_runs(db: Session, job_id: str) -> List[CollectionRun]:
    return list(
        db.execute(
            select(CollectionRun)
            .where(CollectionRun.job_id == job_id)
            .order_by(CollectionRun.run_number.asc())
        )
        .scalars()
        .all()
    )


def get_run_events(db: Session, run_id: str) -> List[ProcessingEvent]:
    return list(
        db.execute(
            select(ProcessingEvent)
            .where(ProcessingEvent.run_id == run_id)
            .order_by(ProcessingEvent.created_at.asc())
        )
        .scalars()
        .all()
    )
