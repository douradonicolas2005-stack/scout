from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.knowledge.dossiers.research_service import record_audit, record_data_change
from app.knowledge.models.domain import (
    Document,
    Entity,
    EntityInteraction,
    Evidence,
    ExtractedClaim,
    RawRecord,
    ResearchSource,
)
from app.knowledge.provenance import VerificationStatus

NATURES = {"declarado", "observado", "interpretado", "a_confirmar"}
INTERACTION_STATUSES = {
    "registered",
    "confirmed",
    "needs_review",
    "contested",
    "cancelled",
    "archived",
}
TIME_PRECISIONS = {"exact", "date", "month", "approximate", "unknown", None}
VERIFICATION_STATUSES = {v.value for v in VerificationStatus}


def ensure_entity(db: Session, entity_id: str) -> Entity:
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise ValueError("entity not found")
    return entity


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _snapshot(obj: EntityInteraction) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "entity_id": obj.entity_id,
        "interaction_type": obj.interaction_type,
        "title": obj.title,
        "description": obj.description,
        "nature": obj.nature,
        "status": obj.status,
        "occurred_at": obj.occurred_at.isoformat() if obj.occurred_at else None,
        "started_at": obj.started_at.isoformat() if obj.started_at else None,
        "ended_at": obj.ended_at.isoformat() if obj.ended_at else None,
        "time_precision": obj.time_precision,
        "channel": obj.channel,
        "location_text": obj.location_text,
        "participants_text": obj.participants_text,
        "source_locator": obj.source_locator,
        "document_id": obj.document_id,
        "research_source_id": obj.research_source_id,
        "raw_record_id": obj.raw_record_id,
        "claim_id": obj.claim_id,
        "evidence_id": obj.evidence_id,
        "confidence": obj.confidence,
        "justification": obj.justification,
        "verification_status": obj.verification_status,
        "metadata_json": obj.metadata_json,
        "created_by": obj.created_by,
    }


def _validate_temporal(started_at: Optional[datetime], ended_at: Optional[datetime]) -> None:
    if started_at and ended_at and ended_at < started_at:
        raise ValueError("ended_at must be greater than or equal to started_at")


def _normalize_nature(value: Optional[str]) -> str:
    v = str(value or "").strip()
    if v not in NATURES:
        raise ValueError("invalid nature")
    return v


def _normalize_status(value: Optional[str], default: str = "registered") -> str:
    v = str(value or default).strip()
    return v if v in INTERACTION_STATUSES else default


def _normalize_time_precision(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    return v if v in TIME_PRECISIONS else None


def _normalize_verification(value: Optional[str], default: str = "nao_verificado") -> str:
    v = str(value or default).strip()
    return v if v in VERIFICATION_STATUSES else default


def _validate_optional_refs(db: Session, payload: Dict[str, Any]) -> None:
    checks = [
        ("document_id", Document, "document"),
        ("research_source_id", ResearchSource, "research source"),
        ("raw_record_id", RawRecord, "raw record"),
        ("claim_id", ExtractedClaim, "claim"),
        ("evidence_id", Evidence, "evidence"),
    ]
    for key, model, label in checks:
        if key not in payload:
            continue
        val = payload.get(key)
        if val is None:
            continue
        if isinstance(val, str) and not val.strip():
            payload[key] = None
            continue
        if db.get(model, val) is None:
            raise ValueError(f"{label} not found")


def create_interaction(
    db: Session, entity_id: str, payload: Dict[str, Any], *, actor: Optional[str] = "local"
) -> EntityInteraction:
    ensure_entity(db, entity_id)
    interaction_type = str(payload.get("interaction_type") or "").strip()
    title = str(payload.get("title") or "").strip()
    if not interaction_type:
        raise ValueError("interaction_type is required")
    if not title:
        raise ValueError("title is required")

    started_at = payload.get("started_at")
    ended_at = payload.get("ended_at")
    _validate_temporal(started_at, ended_at)

    confidence = payload.get("confidence")
    if confidence is not None:
        try:
            c = float(confidence)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("invalid confidence") from exc
        if c < 0.0 or c > 1.0:
            raise ValueError("confidence must be between 0 and 1")
        confidence = c

    _validate_optional_refs(db, payload)

    obj = EntityInteraction(
        entity_id=entity_id,
        interaction_type=interaction_type,
        title=title,
        description=(str(payload["description"]).strip() if payload.get("description") else None),
        nature=_normalize_nature(payload.get("nature")),
        status=_normalize_status(payload.get("status"), "registered"),
        occurred_at=payload.get("occurred_at"),
        started_at=started_at,
        ended_at=ended_at,
        time_precision=_normalize_time_precision(payload.get("time_precision")),
        channel=(str(payload["channel"]).strip() if payload.get("channel") else None),
        location_text=(
            str(payload["location_text"]).strip() if payload.get("location_text") else None
        ),
        participants_text=payload.get("participants_text"),
        source_locator=payload.get("source_locator"),
        document_id=payload.get("document_id"),
        research_source_id=payload.get("research_source_id"),
        raw_record_id=payload.get("raw_record_id"),
        claim_id=payload.get("claim_id"),
        evidence_id=payload.get("evidence_id"),
        confidence=confidence,
        justification=payload.get("justification"),
        verification_status=_normalize_verification(payload.get("verification_status")),
        metadata_json=payload.get("metadata_json"),
        created_by=payload.get("created_by") or actor or "local",
    )
    db.add(obj)
    db.flush()
    record_data_change(
        db,
        entity_table="entity_interactions",
        entity_id=obj.id,
        change_type="create",
        before=None,
        after=_jsonable(_snapshot(obj)),
        reason="dossier.interaction.create",
        actor=actor,
    )
    record_audit(
        db,
        action="dossier.interaction.create",
        target_type="entity_interaction",
        target_id=obj.id,
        details={"entity_id": entity_id, "nature": obj.nature, "type": obj.interaction_type},
        actor_id=actor,
    )
    return obj


def get_interaction(db: Session, interaction_id: str) -> Optional[EntityInteraction]:
    return db.get(EntityInteraction, interaction_id)


@dataclass
class ListInteractionsResult:
    items: List[EntityInteraction]
    total: int


def list_interactions_for_entity(
    db: Session,
    entity_id: str,
    *,
    q: Optional[str] = None,
    interaction_type: Optional[str] = None,
    nature: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort: str = "occurred_desc",
    limit: int = 20,
    offset: int = 0,
) -> ListInteractionsResult:
    stmt = select(EntityInteraction).where(EntityInteraction.entity_id == entity_id)
    count_stmt = (
        select(func.count())
        .select_from(EntityInteraction)
        .where(EntityInteraction.entity_id == entity_id)
    )
    conds = []
    if interaction_type:
        conds.append(EntityInteraction.interaction_type == interaction_type)
    if nature:
        conds.append(EntityInteraction.nature == nature)
    if status:
        conds.append(EntityInteraction.status == status)
    if date_from:
        conds.append(EntityInteraction.occurred_at.is_not(None))
        conds.append(EntityInteraction.occurred_at >= date_from)
    if date_to:
        conds.append(EntityInteraction.occurred_at.is_not(None))
        conds.append(EntityInteraction.occurred_at <= date_to)
    if q:
        like = f"%{q.strip()}%"
        conds.append(
            or_(
                EntityInteraction.title.like(like),
                EntityInteraction.description.like(like),
                EntityInteraction.channel.like(like),
                EntityInteraction.participants_text.like(like),
                EntityInteraction.location_text.like(like),
            )
        )
    if conds:
        stmt = stmt.where(*conds)
        count_stmt = count_stmt.where(*conds)

    sort_map = {
        "occurred_desc": [
            EntityInteraction.occurred_at.desc(),
            EntityInteraction.created_at.desc(),
        ],
        "occurred_asc": [
            EntityInteraction.occurred_at.asc(),
            EntityInteraction.created_at.asc(),
        ],
        "created_desc": [EntityInteraction.created_at.desc(), EntityInteraction.id.asc()],
        "created_asc": [EntityInteraction.created_at.asc(), EntityInteraction.id.asc()],
    }
    stmt = stmt.order_by(
        *sort_map.get(sort, sort_map["occurred_desc"]), EntityInteraction.id.asc()
    )
    stmt = stmt.limit(limit).offset(offset)
    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.execute(stmt).scalars().all())
    return ListInteractionsResult(items=items, total=total)


def update_interaction(
    db: Session, obj: EntityInteraction, payload: Dict[str, Any], *, actor: Optional[str] = "local"
) -> EntityInteraction:
    before = _jsonable(_snapshot(obj))

    _validate_optional_refs(db, payload)

    if "interaction_type" in payload and payload["interaction_type"] is not None:
        v = str(payload["interaction_type"]).strip()
        if not v:
            raise ValueError("interaction_type cannot be empty")
        obj.interaction_type = v
    if "title" in payload and payload["title"] is not None:
        v = str(payload["title"]).strip()
        if not v:
            raise ValueError("title cannot be empty")
        obj.title = v

    for field in [
        "description",
        "occurred_at",
        "started_at",
        "ended_at",
        "channel",
        "location_text",
        "participants_text",
        "source_locator",
        "document_id",
        "research_source_id",
        "raw_record_id",
        "claim_id",
        "evidence_id",
        "justification",
        "metadata_json",
    ]:
        if field in payload:
            setattr(obj, field, payload[field])

    if "nature" in payload and payload["nature"] is not None:
        obj.nature = _normalize_nature(payload["nature"])
    if "status" in payload and payload["status"] is not None:
        obj.status = _normalize_status(payload["status"], obj.status)
    if "time_precision" in payload:
        obj.time_precision = _normalize_time_precision(payload.get("time_precision"))
    if "verification_status" in payload and payload["verification_status"] is not None:
        obj.verification_status = _normalize_verification(
            payload["verification_status"], obj.verification_status
        )
    if "confidence" in payload:
        c = payload.get("confidence")
        if c is None:
            obj.confidence = None
        else:
            cf = float(c)
            if cf < 0.0 or cf > 1.0:
                raise ValueError("confidence must be between 0 and 1")
            obj.confidence = cf

    _validate_temporal(obj.started_at, obj.ended_at)
    db.flush()

    record_data_change(
        db,
        entity_table="entity_interactions",
        entity_id=obj.id,
        change_type="update",
        before=before,
        after=_jsonable(_snapshot(obj)),
        reason="dossier.interaction.update",
        actor=actor,
    )
    record_audit(
        db,
        action="dossier.interaction.update",
        target_type="entity_interaction",
        target_id=obj.id,
        details={"entity_id": obj.entity_id, "nature": obj.nature, "status": obj.status},
        actor_id=actor,
    )
    return obj


def interactions_summary(db: Session, entity_id: str) -> Dict[str, Any]:
    ensure_entity(db, entity_id)
    base = select(func.count()).select_from(EntityInteraction).where(
        EntityInteraction.entity_id == entity_id
    )
    total = int(db.execute(base).scalar_one() or 0)

    def _counts(col: Any) -> Dict[str, int]:
        rows = db.execute(
            select(col, func.count())
            .where(EntityInteraction.entity_id == entity_id)
            .group_by(col)
        ).all()
        return {str(k): int(v) for k, v in rows if k is not None}

    pending = int(
        db.execute(
            select(func.count())
            .select_from(EntityInteraction)
            .where(
                EntityInteraction.entity_id == entity_id,
                or_(
                    EntityInteraction.nature == "a_confirmar",
                    EntityInteraction.status == "needs_review",
                ),
            )
        ).scalar_one()
        or 0
    )
    bounds = db.execute(
        select(
            func.min(EntityInteraction.occurred_at),
            func.max(EntityInteraction.occurred_at),
        ).where(EntityInteraction.entity_id == entity_id)
    ).one()
    return {
        "entity_id": entity_id,
        "interactions_count": total,
        "pending_confirmation_or_review": pending,
        "by_nature": _counts(EntityInteraction.nature),
        "by_type": _counts(EntityInteraction.interaction_type),
        "by_status": _counts(EntityInteraction.status),
        "earliest_occurred_at": bounds[0],
        "latest_occurred_at": bounds[1],
    }
