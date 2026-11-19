from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.schemas.audit import AuditEventListResponse, AuditEventResponse
from app.db.session import get_db
from app.knowledge.models.domain import AuditEvent

router = APIRouter()


@router.get("/system/audit-events", response_model=AuditEventListResponse)
def list_audit_events(
    limit: int = Query(default=50, ge=1, le=200),
    target_type: Optional[str] = Query(default=None),
    target_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> AuditEventListResponse:
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    if target_type:
        stmt = stmt.where(AuditEvent.target_type == target_type)
    if target_id:
        stmt = stmt.where(AuditEvent.target_id == target_id)
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    rows = db.execute(stmt).scalars().all()
    return AuditEventListResponse(items=[AuditEventResponse.model_validate(r) for r in rows])
