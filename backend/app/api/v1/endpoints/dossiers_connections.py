from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.dossiers_connections import (
    ConnectionCreate,
    ConnectionDetail,
    ConnectionEntitySummary,
    ConnectionListResponse,
    ConnectionSummary,
    ConnectionSummaryResponse,
    ConnectionTaxonomyResponse,
    ConnectionUpdate,
    TaxonomyRelationType,
)
from app.db.session import get_db
from app.knowledge.dossiers.connections_service import (
    D4ConflictError,
    D4NotFoundError,
    D4ValidationError,
    connections_summary,
    create_connection,
    ensure_entity,
    get_connection,
    list_connections_for_entity,
    update_connection,
)
from app.knowledge.dossiers.connections_taxonomy import SPECS
from app.knowledge.models.domain import Entity, Relationship

router = APIRouter(prefix="/dossiers", tags=["dossiers"])


def _entity_summary(entity: Optional[Entity]) -> Optional[ConnectionEntitySummary]:
    if entity is None:
        return None
    return ConnectionEntitySummary(
        id=entity.id,
        canonical_name=entity.canonical_name,
        entity_type=entity.entity_type,
        profile_status=getattr(entity, "profile_status", None),
    )


def _taxonomy_meta(relation_type: str):
    return SPECS.get(relation_type)


def _perspective_for_anchor(obj: Relationship, anchor_entity_id: str) -> str:
    if obj.directionality == "undirected":
        return "undirected"
    if obj.from_entity_id == anchor_entity_id:
        return "outgoing"
    if obj.to_entity_id == anchor_entity_id:
        return "incoming"
    return "undirected"


def _perspective_label(obj: Relationship, anchor_entity_id: Optional[str]) -> Optional[str]:
    spec = _taxonomy_meta(obj.relation_type)
    if spec is None:
        return None
    if obj.directionality == "undirected":
        return spec.symmetric_label or spec.name
    if anchor_entity_id is None:
        return spec.name
    persp = _perspective_for_anchor(obj, anchor_entity_id)
    if persp == "outgoing":
        return spec.name
    if persp == "incoming":
        return spec.inverse_label or spec.name
    return spec.name


def _has_evidence(obj: Relationship) -> bool:
    return bool(obj.claim_id or obj.evidence_id or (obj.source_locator and str(obj.source_locator).strip()))


def _enrich_connection(
    db: Session, obj: Relationship, anchor_entity_id: Optional[str] = None
) -> dict:
    from_entity = db.get(Entity, obj.from_entity_id)
    to_entity = db.get(Entity, obj.to_entity_id)
    spec = _taxonomy_meta(obj.relation_type)
    persp = _perspective_for_anchor(obj, anchor_entity_id) if anchor_entity_id else None
    counterpart = None
    if anchor_entity_id:
        if obj.directionality == "undirected":
            other_id = obj.to_entity_id if obj.from_entity_id == anchor_entity_id else obj.from_entity_id
            counterpart = db.get(Entity, other_id)
        elif persp == "outgoing":
            counterpart = to_entity
        elif persp == "incoming":
            counterpart = from_entity
        else:
            counterpart = None
    return {
        "id": obj.id,
        "from_entity_id": obj.from_entity_id,
        "to_entity_id": obj.to_entity_id,
        "relation_type": obj.relation_type,
        "relation_type_name": spec.name if spec else None,
        "category": spec.category if spec else None,
        "directionality": obj.directionality,
        "nature": obj.nature,
        "verification_status": obj.verification_status,
        "status": obj.status,
        "occurred_at": obj.occurred_at,
        "valid_from": obj.valid_from,
        "valid_to": obj.valid_to,
        "time_precision": obj.time_precision,
        "confidence": obj.confidence,
        "claim_id": obj.claim_id,
        "evidence_id": obj.evidence_id,
        "source_locator": obj.source_locator,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "description": obj.description,
        "justification": obj.justification,
        "attributes_json": obj.attributes_json,
        "created_by": obj.created_by,
        "inverse_label": spec.inverse_label if spec else None,
        "symmetric_label": spec.symmetric_label if spec else None,
        "inverse_type_id": spec.inverse_type_id if spec else None,
        "from_entity": _entity_summary(from_entity),
        "to_entity": _entity_summary(to_entity),
        "counterpart_entity": _entity_summary(counterpart),
        "perspective": persp,
        "perspective_label": _perspective_label(obj, anchor_entity_id),
        "has_evidence": _has_evidence(obj),
    }


def _raise_d4(exc: Exception) -> None:
    if isinstance(exc, D4NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, D4ConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if isinstance(exc, D4ValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc
    raise exc


@router.get("/connections/taxonomy", response_model=ConnectionTaxonomyResponse)
def get_connections_taxonomy() -> ConnectionTaxonomyResponse:
    items = [
        TaxonomyRelationType(
            id=s.id,
            category=s.category,
            name=s.name,
            description=s.description,
            directionality=s.directionality,  # type: ignore[arg-type]
            from_entity_types=sorted(list(s.from_entity_types)),
            to_entity_types=sorted(list(s.to_entity_types)),
            status_mvp=s.status_mvp,
            inverse_label=s.inverse_label,
            symmetric_label=s.symmetric_label,
            inverse_type_id=s.inverse_type_id,
            notes=s.notes,
        )
        for s in SPECS.values()
    ]
    items.sort(key=lambda x: (x.category, x.id))
    approved = sum(1 for x in items if x.status_mvp == "approved")
    return ConnectionTaxonomyResponse(items=items, approved_count=approved, total=len(items))


@router.post(
    "/entities/{entity_id}/connections",
    response_model=ConnectionDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_connection_endpoint(
    entity_id: str, payload: ConnectionCreate, db: Session = Depends(get_db)
) -> ConnectionDetail:
    try:
        obj = create_connection(db, entity_id, payload.model_dump())
        db.commit()
        db.refresh(obj)
        return ConnectionDetail.model_validate(_enrich_connection(db, obj, anchor_entity_id=entity_id))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        _raise_d4(exc)
        raise  # unreachable


@router.get("/entities/{entity_id}/connections", response_model=ConnectionListResponse)
def list_connections_endpoint(
    entity_id: str,
    db: Session = Depends(get_db),
    direction: Optional[str] = Query(default=None),
    relation_type: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    nature: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    occurred_from: Optional[datetime] = Query(default=None),
    occurred_to: Optional[datetime] = Query(default=None),
    valid_from: Optional[datetime] = Query(default=None),
    valid_to: Optional[datetime] = Query(default=None),
    has_evidence: Optional[bool] = Query(default=None),
    q: Optional[str] = Query(default=None),
    sort: str = Query(default="updated_desc"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ConnectionListResponse:
    try:
        ensure_entity(db, entity_id)
        result = list_connections_for_entity(
            db,
            entity_id,
            direction=direction,
            relation_type=relation_type,
            category=category,
            nature=nature,
            verification_status=verification_status,
            status=status_filter,
            occurred_from=occurred_from,
            occurred_to=occurred_to,
            valid_from=valid_from,
            valid_to=valid_to,
            has_evidence=has_evidence,
            q=q,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return ConnectionListResponse(
            items=[
                ConnectionSummary.model_validate(_enrich_connection(db, x, anchor_entity_id=entity_id))
                for x in result.items
            ],
            total=result.total,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:  # noqa: BLE001
        _raise_d4(exc)
        raise


@router.get("/connections/{connection_id}", response_model=ConnectionDetail)
def get_connection_endpoint(
    connection_id: str,
    db: Session = Depends(get_db),
    anchor_entity_id: Optional[str] = Query(default=None),
) -> ConnectionDetail:
    obj = get_connection(db, connection_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found")
    if anchor_entity_id:
        ensure_entity(db, anchor_entity_id)
    return ConnectionDetail.model_validate(_enrich_connection(db, obj, anchor_entity_id=anchor_entity_id))


@router.patch("/connections/{connection_id}", response_model=ConnectionDetail)
def update_connection_endpoint(
    connection_id: str,
    payload: ConnectionUpdate,
    db: Session = Depends(get_db),
    anchor_entity_id: Optional[str] = Query(default=None),
) -> ConnectionDetail:
    obj = get_connection(db, connection_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="connection not found")
    if anchor_entity_id:
        ensure_entity(db, anchor_entity_id)
    try:
        obj = update_connection(db, obj, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(obj)
        return ConnectionDetail.model_validate(_enrich_connection(db, obj, anchor_entity_id=anchor_entity_id))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        _raise_d4(exc)
        raise


@router.get("/entities/{entity_id}/connections/summary", response_model=ConnectionSummaryResponse)
def connections_summary_endpoint(
    entity_id: str, db: Session = Depends(get_db)
) -> ConnectionSummaryResponse:
    try:
        data = connections_summary(db, entity_id)
        return ConnectionSummaryResponse.model_validate(data)
    except Exception as exc:  # noqa: BLE001
        _raise_d4(exc)
        raise
