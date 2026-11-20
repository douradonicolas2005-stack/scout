from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api.v1.schemas.system import (
    DbStatusResponse,
    DbTableStat,
    ModuleStatus,
    SystemInfoResponse,
)
from app.core.config import settings
from app.db.session import get_db

router = APIRouter()

MODULES: List[ModuleStatus] = [
    ModuleStatus(key="radar", label="Radar", path="/radar"),
    ModuleStatus(
        key="dossiers",
        label="Dossiers",
        path="/dossiers",
        status="in_development",
        implemented=True,
    ),
    ModuleStatus(key="knowledge-graph", label="Knowledge Graph", path="/knowledge-graph"),
    ModuleStatus(key="predictions", label="Predictions", path="/predictions"),
    ModuleStatus(key="scenario-lab", label="Scenario Lab", path="/scenario-lab"),
    ModuleStatus(key="action-center", label="Action Center", path="/action-center"),
    ModuleStatus(key="agent-control", label="Agent Control", path="/agent-control"),
    ModuleStatus(key="system", label="System", path="/system"),
]


@router.get("/system/info", response_model=SystemInfoResponse)
def system_info() -> SystemInfoResponse:
    return SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        phase="foundation-g",
        environment=settings.environment,
        ollama={
            "base_url": settings.ollama_base_url,
            "model": settings.ollama_model,
            "mode": "abstraction-availability-only",
        },
        scheduler={
            "enabled": settings.scheduler_enabled,
            "max_concurrent_jobs": settings.scheduler_max_concurrent_jobs,
            "state": "db-canonical" if settings.scheduler_enabled else "db-canonical-ready",
        },
        modules=MODULES,
        timestamp=datetime.now(timezone.utc),
    )


def _get_alembic_revisions(db: Session) -> List[str]:
    try:
        rows = db.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        return [str(r[0]) for r in rows if r[0] is not None]
    except Exception:  # noqa: BLE001
        return []


@router.get("/db/status", response_model=DbStatusResponse)
def db_status(db: Session = Depends(get_db)) -> DbStatusResponse:
    try:
        db.execute(text("SELECT 1"))
        bind = db.get_bind()
        inspector = inspect(bind)
        table_names = sorted(inspector.get_table_names())
        tables: List[DbTableStat] = []
        for name in table_names:
            try:
                count = db.execute(text(f'SELECT COUNT(*) FROM "{name}"')).scalar_one()
            except Exception:  # noqa: BLE001
                count = 0
            tables.append(DbTableStat(name=name, row_count=int(count)))

        dialect = bind.dialect.name if bind is not None else "unknown"
        foreign_keys = None
        journal_mode = None
        busy_timeout = None
        if dialect == "sqlite":
            try:
                foreign_keys = int(db.execute(text("PRAGMA foreign_keys")).scalar_one())
            except Exception:  # noqa: BLE001
                foreign_keys = None
            try:
                journal_mode = str(db.execute(text("PRAGMA journal_mode")).scalar_one())
            except Exception:  # noqa: BLE001
                journal_mode = None
            try:
                busy_timeout = int(db.execute(text("PRAGMA busy_timeout")).scalar_one())
            except Exception:  # noqa: BLE001
                busy_timeout = None

        revisions = _get_alembic_revisions(db)
        if bind is None:
            db_url = settings.resolved_database_url
        else:
            engine_obj = bind.engine if hasattr(bind, "engine") else bind
            db_url = str(getattr(engine_obj, "url", settings.resolved_database_url))
        # redact absolute path details not necessary, but local-only; keep simple
        return DbStatusResponse(
            connected=True,
            dialect=dialect,
            database_url=db_url,
            table_count=len(table_names),
            tables=tables,
            alembic_revision=revisions[0] if revisions else None,
            alembic_revisions=revisions,
            foreign_keys=foreign_keys,
            journal_mode=journal_mode,
            busy_timeout=busy_timeout,
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as exc:  # noqa: BLE001
        return DbStatusResponse(
            connected=False,
            dialect="unknown",
            database_url=settings.resolved_database_url,
            table_count=0,
            tables=[],
            error=f"{exc.__class__.__name__}: {exc}",
            timestamp=datetime.now(timezone.utc),
        )
