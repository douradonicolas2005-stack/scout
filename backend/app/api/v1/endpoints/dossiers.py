from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.dossiers import (
    DuplicateCandidate,
    DuplicateCandidatesResponse,
    EntityAliasResponse,
    EntityCreate,
    EntityDetailResponse,
    EntityIdentifierResponse,
    EntityListResponse,
    EntitySummaryResponse,
    EntityUpdate,
)
from app.db.session import get_db
from app.knowledge.dossiers.service import (
    create_entity,
    find_duplicate_candidates,
    get_entity,
    list_entities,
    load_aliases,
    load_identifiers,
    update_entity,
)
from app.knowledge.models.domain import Entity

router = APIRouter(prefix="/dossiers", tags=["dossiers"])


def _to_summary(entity: Entity) -> EntitySummaryResponse:
    return EntitySummaryResponse.model_validate(entity, from_attributes=True)


def _to_detail(db: Session, entity: Entity) -> EntityDetailResponse:
    identifiers = load_identifiers(db, entity.id)
    aliases = load_aliases(db, entity.id)
    ident_resp = [
        EntityIdentifierResponse.model_validate(i, from_attributes=True) for i in identifiers
    ]
    alias_resp = [EntityAliasResponse.model_validate(a, from_attributes=True) for a in aliases]
    return EntityDetailResponse(
        id=entity.id,
        entity_type=entity.entity_type,
        canonical_name=entity.canonical_name,
        normalized_name=entity.normalized_name,
        description=entity.description,
        profile_status=entity.profile_status,
        primary_location=entity.primary_location,
        verification_status=entity.verification_status,
        confidence=entity.confidence,
        source_first_id=entity.source_first_id,
        first_seen_at=entity.first_seen_at,
        last_seen_at=entity.last_seen_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        profile_data=entity.profile_data,
        attributes_json=entity.attributes_json,
        identifiers=ident_resp,
        aliases=alias_resp,
    )


@router.post(
    "/entities",
    response_model=EntityDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_entity_endpoint(
    payload: EntityCreate, db: Session = Depends(get_db)
) -> EntityDetailResponse:
    try:
        entity = create_entity(db, payload.model_dump(exclude_unset=False))
        db.commit()
        db.refresh(entity)
        return _to_detail(db, entity)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/entities", response_model=EntityListResponse)
def list_entities_endpoint(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    profile_status: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    updated_from: Optional[datetime] = Query(default=None),
    updated_to: Optional[datetime] = Query(default=None),
    sort: str = Query(default="updated_desc"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> EntityListResponse:
    result = list_entities(
        db,
        q=q,
        entity_type=entity_type,
        profile_status=profile_status,
        verification_status=verification_status,
        updated_from=updated_from,
        updated_to=updated_to,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return EntityListResponse(
        items=[_to_summary(e) for e in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/entities/{entity_id}", response_model=EntityDetailResponse)
def get_entity_endpoint(entity_id: str, db: Session = Depends(get_db)) -> EntityDetailResponse:
    entity = get_entity(db, entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    return _to_detail(db, entity)


@router.patch("/entities/{entity_id}", response_model=EntityDetailResponse)
def update_entity_endpoint(
    entity_id: str, payload: EntityUpdate, db: Session = Depends(get_db)
) -> EntityDetailResponse:
    entity = get_entity(db, entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    try:
        entity = update_entity(db, entity, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(entity)
        return _to_detail(db, entity)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get(
    "/entities/{entity_id}/duplicate-candidates",
    response_model=DuplicateCandidatesResponse,
)
def duplicate_candidates_endpoint(
    entity_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50),
) -> DuplicateCandidatesResponse:
    entity = get_entity(db, entity_id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")
    candidates = find_duplicate_candidates(db, entity, limit=limit)
    return DuplicateCandidatesResponse(
        entity_id=entity_id,
        items=[
            DuplicateCandidate(
                candidate=_to_summary(c.entity),
                score_level=c.score_level,
                reasons=c.reasons,
            )
            for c in candidates
        ],
    )
