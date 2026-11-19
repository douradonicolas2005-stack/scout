from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.ingestion import (
    ConnectorListResponse,
    ConnectorResponse,
    SourceCreate,
    SourceListResponse,
    SourceResponse,
    SourceTestConnectionResponse,
    SourceUpdate,
)
from app.db.session import get_db
from app.ingestion.bootstrap import (
    ensure_builtin_connectors_registered,
    sync_builtin_connectors_to_db,
)
from app.ingestion.registry import get_connector_class
from app.knowledge.models.domain import AuditEvent, Connector, ProcessingEvent, Source

router = APIRouter()


def _record_audit(
    db: Session,
    *,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    severity: str = "info",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    db.add(
        AuditEvent(
            actor_type="system",
            actor_id="api",
            action=action,
            target_type=target_type,
            target_id=target_id,
            severity=severity,
            details_json=details or {},
            ip_or_origin="127.0.0.1",
        )
    )


def _connector_to_response(conn: Connector) -> ConnectorResponse:
    return ConnectorResponse(
        id=conn.id,
        key=conn.key,
        name=conn.name,
        version=conn.version,
        capabilities=conn.capabilities_json,
        config_schema=conn.config_schema_json,
        status=conn.status,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


@router.get("/ingestion/connectors", response_model=ConnectorListResponse)
def list_connectors(db: Session = Depends(get_db)) -> ConnectorListResponse:
    sync_builtin_connectors_to_db(db)
    rows = db.execute(select(Connector).order_by(Connector.key.asc())).scalars().all()
    return ConnectorListResponse(items=[_connector_to_response(r) for r in rows])


@router.get("/ingestion/connectors/{connector_key}", response_model=ConnectorResponse)
def get_connector(connector_key: str, db: Session = Depends(get_db)) -> ConnectorResponse:
    sync_builtin_connectors_to_db(db)
    row = db.execute(select(Connector).where(Connector.key == connector_key)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    return _connector_to_response(row)


@router.post(
    "/ingestion/sources",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    payload: SourceCreate, db: Session = Depends(get_db)
) -> SourceResponse:
    ensure_builtin_connectors_registered()
    if get_connector_class(payload.connection_type) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown connector/connection_type: {payload.connection_type}",
        )
    # Validate config early when connector exists
    if payload.config_json is not None:
        cls = get_connector_class(payload.connection_type)
        if cls is not None:
            try:
                cls().validate_config(payload.config_json)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid source config: {exc}",
                ) from exc

    source = Source(
        name=payload.name,
        category=payload.category,
        description=payload.description,
        resource_locator=payload.resource_locator,
        connection_type=payload.connection_type,
        auth_method=payload.auth_method,
        auth_credential_ref=payload.auth_credential_ref,
        frequency=payload.frequency,
        status=payload.status,
        config_json=payload.config_json,
        permissions_json=payload.permissions_json,
        terms_conditions=payload.terms_conditions,
        is_active=payload.is_active,
        created_by=payload.created_by,
    )
    db.add(source)
    db.flush()
    _record_audit(
        db,
        action="source.create",
        target_type="source",
        target_id=source.id,
        details={"connection_type": source.connection_type, "name": source.name},
    )
    db.commit()
    db.refresh(source)
    return SourceResponse.model_validate(source)


@router.get("/ingestion/sources", response_model=SourceListResponse)
def list_sources(
    active_only: bool = Query(default=False, description="Return only active sources"),
    db: Session = Depends(get_db),
) -> SourceListResponse:
    stmt = select(Source).order_by(Source.created_at.desc())
    if active_only:
        stmt = stmt.where(Source.is_active.is_(True))
    rows = db.execute(stmt).scalars().all()
    return SourceListResponse(items=[SourceResponse.model_validate(r) for r in rows])


@router.get("/ingestion/sources/{source_id}", response_model=SourceResponse)
def get_source(source_id: str, db: Session = Depends(get_db)) -> SourceResponse:
    row = db.get(Source, source_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return SourceResponse.model_validate(row)


@router.patch("/ingestion/sources/{source_id}", response_model=SourceResponse)
def update_source(
    source_id: str, payload: SourceUpdate, db: Session = Depends(get_db)
) -> SourceResponse:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    data = payload.model_dump(exclude_unset=True)
    new_connection_type = data.get("connection_type", source.connection_type)
    ensure_builtin_connectors_registered()
    if new_connection_type and get_connector_class(new_connection_type) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown connector/connection_type: {new_connection_type}",
        )

    # Validate config if provided or if connection type changes
    if "config_json" in data or "connection_type" in data:
        cfg = data.get("config_json", source.config_json)
        if cfg is not None:
            cls = get_connector_class(new_connection_type)
            if cls is not None:
                try:
                    cls().validate_config(cfg)
                except Exception as exc:  # noqa: BLE001
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid source config: {exc}",
                    ) from exc

    for field, value in data.items():
        setattr(source, field, value)

    # keep status/is_active coherent when one is provided
    if "is_active" in data and "status" not in data:
        source.status = "active" if source.is_active else "inactive"
    if "status" in data and "is_active" not in data and data["status"] in {"active", "inactive"}:
        source.is_active = data["status"] == "active"

    _record_audit(
        db,
        action="source.update",
        target_type="source",
        target_id=source.id,
        details={"updated_fields": sorted(list(data.keys()))},
    )
    db.commit()
    db.refresh(source)
    return SourceResponse.model_validate(source)


@router.post(
    "/ingestion/sources/{source_id}/test-connection",
    response_model=SourceTestConnectionResponse,
)
def test_source_connection(
    source_id: str, db: Session = Depends(get_db)
) -> SourceTestConnectionResponse:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    ensure_builtin_connectors_registered()
    cls = get_connector_class(source.connection_type)
    if cls is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown connector/connection_type: {source.connection_type}",
        )

    connector = cls()
    cfg = dict(source.config_json or {})
    # Ensure locator is available to connector (common convention)
    if "url" not in cfg and source.resource_locator:
        cfg["url"] = source.resource_locator

    try:
        result = connector.test_connection(cfg)
    except Exception as exc:  # noqa: BLE001
        result_ok = False
        result_message = f"{exc.__class__.__name__}: {exc}"
        result_metadata: Dict[str, Any] = {}
    else:
        result_ok = bool(result.ok)
        result_message = result.message
        result_metadata = result.metadata or {}

    tested_at = datetime.now(timezone.utc)
    # Minimal traceability: audit + processing event (no pipeline run/job in Subetapa E)
    _record_audit(
        db,
        action="source.test_connection",
        target_type="source",
        target_id=source.id,
        severity="info" if result_ok else "warning",
        details={
            "ok": result_ok,
            "connector_key": source.connection_type,
            "message": result_message,
        },
    )
    db.add(
        ProcessingEvent(
            stage="connection_test",
            status="succeeded" if result_ok else "failed",
            message=result_message,
            payload_json={
                "source_id": source.id,
                "connector_key": source.connection_type,
                "ok": result_ok,
                "metadata": result_metadata,
            },
        )
    )
    db.commit()

    return SourceTestConnectionResponse(
        source_id=source.id,
        connector_key=source.connection_type,
        ok=result_ok,
        message=result_message,
        metadata=result_metadata,
        tested_at=tested_at,
    )
