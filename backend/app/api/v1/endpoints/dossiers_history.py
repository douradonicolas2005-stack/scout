from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.dossiers_history import (
    InteractionCreate,
    InteractionDetail,
    InteractionListResponse,
    InteractionSummary,
    InteractionSummaryResponse,
    InteractionUpdate,
)
from app.db.session import get_db
from app.knowledge.dossiers.history_service import (
    create_interaction,
    get_interaction,
    interactions_summary,
    list_interactions_for_entity,
    update_interaction,
)
from app.knowledge.dossiers.service import get_entity

router = APIRouter(prefix="/dossiers", tags=["dossiers"])


def _ensure_entity_exists(db: Session, entity_id: str) -> None:
    if get_entity(db, entity_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")


@router.post(
    "/entities/{entity_id}/interactions",
    response_model=InteractionDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_interaction_endpoint(
    entity_id: str, payload: InteractionCreate, db: Session = Depends(get_db)
) -> InteractionDetail:
    _ensure_entity_exists(db, entity_id)
    try:
        obj = create_interaction(db, entity_id, payload.model_dump())
        db.commit()
        db.refresh(obj)
        return InteractionDetail.model_validate(obj)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc


@router.get("/entities/{entity_id}/interactions", response_model=InteractionListResponse)
def list_interactions_endpoint(
    entity_id: str,
    db: Session = Depends(get_db),
    q: Optional[str] = Query(default=None),
    interaction_type: Optional[str] = Query(default=None),
    nature: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    sort: str = Query(default="occurred_desc"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> InteractionListResponse:
    _ensure_entity_exists(db, entity_id)
    result = list_interactions_for_entity(
        db,
        entity_id,
        q=q,
        interaction_type=interaction_type,
        nature=nature,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return InteractionListResponse(
        items=[InteractionSummary.model_validate(x) for x in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/interactions/{interaction_id}", response_model=InteractionDetail)
def get_interaction_endpoint(
    interaction_id: str, db: Session = Depends(get_db)
) -> InteractionDetail:
    obj = get_interaction(db, interaction_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return InteractionDetail.model_validate(obj)


@router.patch("/interactions/{interaction_id}", response_model=InteractionDetail)
def update_interaction_endpoint(
    interaction_id: str, payload: InteractionUpdate, db: Session = Depends(get_db)
) -> InteractionDetail:
    obj = get_interaction(db, interaction_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    try:
        obj = update_interaction(db, obj, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(obj)
        return InteractionDetail.model_validate(obj)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc


@router.get(
    "/entities/{entity_id}/interactions/summary", response_model=InteractionSummaryResponse
)
def interactions_summary_endpoint(
    entity_id: str, db: Session = Depends(get_db)
) -> InteractionSummaryResponse:
    _ensure_entity_exists(db, entity_id)
    try:
        data = interactions_summary(db, entity_id)
        return InteractionSummaryResponse.model_validate(data)
    except ValueError as exc:
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc
