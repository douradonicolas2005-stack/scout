"""Scheduler integration (Subetapa F).

APScheduler-backed dispatch with DB-canonical state. Scheduling is conservative and
disabled by default. Pending/runnable jobs live in the database; the scheduler only
dispatches execution ticks that pick work from DB (no in-memory canonical state).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal
from app.knowledge.models.domain import CollectionJob

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IngestionScheduler:
    def __init__(
        self,
        *,
        enabled: bool = False,
        max_concurrent_jobs: int = 1,
        session_factory: sessionmaker[Session] = SessionLocal,
        poll_seconds: int = 30,
        executor: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.enabled = enabled
        self.max_concurrent_jobs = max(1, int(max_concurrent_jobs))
        self._session_factory = session_factory
        self._poll_seconds = max(5, int(poll_seconds))
        self._scheduler: Optional[BackgroundScheduler] = None
        self._executor = executor
        self._dispatching = False

    def _job_executor(self, job_id: str) -> None:
        if self._executor is not None:
            self._executor(job_id)
            return
        # Local import to avoid circular dependency at module import time
        from app.ingestion.collection import execute_collection_job

        db = self._session_factory()
        try:
            execute_collection_job(db, job_id)
        finally:
            db.close()

    def _dispatch_once(self) -> None:
        """Pick and execute runnable jobs from DB (canonical state)."""
        if not self.enabled or self._dispatching:
            return
        self._dispatching = True
        try:
            db = self._session_factory()
            try:
                # Rehydrate/process pending jobs; run conservatively (one at a time).
                while True:
                    active_count = db.execute(
                        select(CollectionJob.id).where(CollectionJob.status == "running")
                    ).scalars().all()
                    if len(active_count) >= self.max_concurrent_jobs:
                        return

                    now = _utcnow()
                    stmt = (
                        select(CollectionJob)
                        .where(CollectionJob.status == "pending")
                        .where(
                            or_(
                                CollectionJob.scheduled_for.is_(None),
                                CollectionJob.scheduled_for <= now,
                            )
                        )
                        .order_by(
                            CollectionJob.priority.desc(),
                            CollectionJob.scheduled_for.asc().nullsfirst(),
                            CollectionJob.created_at.asc(),
                        )
                        .limit(1)
                    )
                    job = db.execute(stmt).scalars().first()
                    if job is None:
                        return
                    job_id = job.id
                    # release session before execution (executor uses its own session)
                    db.expunge(job)
                    self._job_executor(job_id)
            finally:
                db.close()
        except Exception:  # noqa: BLE001
            logger.exception("Scheduler dispatch tick failed")
        finally:
            self._dispatching = False

    def start(self) -> None:
        if not self.enabled:
            logger.info("Ingestion scheduler disabled (foundation-g)")
            return
        if self._scheduler and self._scheduler.running:
            return
        self._scheduler = BackgroundScheduler(
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 60,
            }
        )
        self._scheduler.add_job(
            self._dispatch_once,
            trigger="interval",
            seconds=self._poll_seconds,
            id="ingestion_dispatch",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(
            "Ingestion scheduler started (poll=%ss, max_concurrent_jobs=%s)",
            self._poll_seconds,
            self.max_concurrent_jobs,
        )
        # Controlled rehydration: process pending jobs from DB-canonical state.
        try:
            self._dispatch_once()
        except Exception:  # noqa: BLE001
            logger.exception("Initial scheduler rehydration dispatch failed")

    def shutdown(self) -> None:
        if self._scheduler:
            try:
                self._scheduler.shutdown(wait=False)
            except Exception:  # noqa: BLE001
                logger.exception("Scheduler shutdown failed")
        self._scheduler = None
        self._dispatching = False

    @property
    def running(self) -> bool:
        return bool(self._scheduler and self._scheduler.running)


_scheduler: Optional[IngestionScheduler] = None


def get_scheduler(
    enabled: bool = False, max_concurrent_jobs: int = 1
) -> IngestionScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = IngestionScheduler(
            enabled=enabled, max_concurrent_jobs=max_concurrent_jobs
        )
    else:
        # keep singleton but allow config refresh before start
        _scheduler.enabled = enabled
        _scheduler.max_concurrent_jobs = max(1, int(max_concurrent_jobs))
    return _scheduler


def reset_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        try:
            _scheduler.shutdown()
        except Exception:  # noqa: BLE001
            pass
    _scheduler = None
