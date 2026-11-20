from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.knowledge.models.domain import (
    AuditEvent,
    DataChange,
    Entity,
    EntityAlias,
    EntityIdentifier,
)

SUPPORTED_ENTITY_TYPES = {"person", "company", "economic_group", "institution", "other"}
PROFILE_STATUSES = {"active", "archived", "pending"}


def normalize_text(value: str) -> str:
    v = unicodedata.normalize("NFKD", value or "")
    v = "".join(ch for ch in v if not unicodedata.combining(ch))
    v = v.lower().strip()
    # remove punctuation/symbol noise while preserving word boundaries
    v = re.sub(r"[^a-z0-9\s]+", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    return v


def normalize_identifier(value: str) -> str:
    v = normalize_text(value)
    v = re.sub(r"[^a-z0-9]+", "", v)
    return v


def _entity_snapshot(
    entity: Entity,
    identifiers: Sequence[EntityIdentifier],
    aliases: Sequence[EntityAlias],
) -> Dict[str, Any]:
    return {
        "id": entity.id,
        "entity_type": entity.entity_type,
        "canonical_name": entity.canonical_name,
        "normalized_name": entity.normalized_name,
        "description": entity.description,
        "profile_status": entity.profile_status,
        "primary_location": entity.primary_location,
        "profile_data": entity.profile_data,
        "attributes_json": entity.attributes_json,
        "confidence": entity.confidence,
        "verification_status": entity.verification_status,
        "first_seen_at": entity.first_seen_at.isoformat() if entity.first_seen_at else None,
        "last_seen_at": entity.last_seen_at.isoformat() if entity.last_seen_at else None,
        "source_first_id": entity.source_first_id,
        "identifiers": [
            {
                "id_type": i.id_type,
                "value": i.value,
                "normalized_value": i.normalized_value,
                "is_primary": i.is_primary,
            }
            for i in identifiers
        ],
        "aliases": [
            {
                "name": a.name,
                "normalized_name": a.normalized_name,
                "alias_type": a.alias_type,
            }
            for a in aliases
        ],
    }


def record_audit(
    db: Session,
    *,
    action: str,
    target_id: Optional[str] = None,
    target_type: str = "entity",
    severity: str = "info",
    details: Optional[Dict[str, Any]] = None,
    actor_type: str = "user",
    actor_id: Optional[str] = "local",
) -> None:
    db.add(
        AuditEvent(
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            severity=severity,
            details_json=details or {},
            ip_or_origin="127.0.0.1",
        )
    )


def record_data_change(
    db: Session,
    *,
    entity_id: str,
    change_type: str,
    before: Optional[Dict[str, Any]],
    after: Optional[Dict[str, Any]],
    reason: Optional[str] = None,
    actor: Optional[str] = "local",
) -> None:
    db.add(
        DataChange(
            entity_table="entities",
            entity_id=entity_id,
            change_type=change_type,
            before_json=before,
            after_json=after,
            reason=reason,
            actor=actor,
        )
    )


def load_identifiers(db: Session, entity_id: str) -> List[EntityIdentifier]:
    stmt = (
        select(EntityIdentifier)
        .where(EntityIdentifier.entity_id == entity_id)
        .order_by(EntityIdentifier.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def load_aliases(db: Session, entity_id: str) -> List[EntityAlias]:
    stmt = (
        select(EntityAlias)
        .where(EntityAlias.entity_id == entity_id)
        .order_by(EntityAlias.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def replace_identifiers(
    db: Session, entity: Entity, items: Iterable[Dict[str, Any]]
) -> List[EntityIdentifier]:
    db.query(EntityIdentifier).filter(
        EntityIdentifier.entity_id == entity.id
    ).delete(synchronize_session=False)
    out: List[EntityIdentifier] = []
    for item in items:
        value = str(item.get("value", "")).strip()
        if not value:
            continue
        raw_type = item.get("id_type")
        id_type = str(raw_type or "external_id").strip() or "external_id"
        norm = normalize_identifier(value) or normalize_text(value)
        ident = EntityIdentifier(
            entity_id=entity.id,
            id_type=id_type,
            value=value,
            normalized_value=norm,
            is_primary=bool(item.get("is_primary", False)),
            metadata_json=item.get("metadata_json"),
        )
        db.add(ident)
        out.append(ident)
    return out


def replace_aliases(
    db: Session, entity: Entity, items: Iterable[Dict[str, Any]]
) -> List[EntityAlias]:
    db.query(EntityAlias).filter(
        EntityAlias.entity_id == entity.id
    ).delete(synchronize_session=False)
    out: List[EntityAlias] = []
    for item in items:
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        raw_alias_type = item.get("alias_type")
        alias_type = str(raw_alias_type).strip() if raw_alias_type else None
        alias = EntityAlias(
            entity_id=entity.id,
            name=name,
            normalized_name=normalize_text(name),
            alias_type=alias_type,
        )
        db.add(alias)
        out.append(alias)
    return out


def create_entity(db: Session, payload: Dict[str, Any]) -> Entity:
    entity_type = str(payload.get("entity_type") or "").strip() or "other"
    name = str(payload.get("canonical_name") or "").strip()
    if not name:
        raise ValueError("canonical_name is required")
    profile_status = str(payload.get("profile_status") or "active")
    if profile_status not in PROFILE_STATUSES:
        profile_status = "active"
    now = payload.get("now")
    entity = Entity(
        entity_type=entity_type,
        canonical_name=name,
        normalized_name=normalize_text(name),
        description=payload.get("description"),
        profile_status=profile_status,
        primary_location=payload.get("primary_location"),
        profile_data=payload.get("profile_data"),
        attributes_json=payload.get("attributes_json"),
        confidence=payload.get("confidence"),
        verification_status=str(payload.get("verification_status") or "nao_verificado"),
        source_first_id=payload.get("source_first_id"),
        first_seen_at=payload.get("first_seen_at") or now,
        last_seen_at=payload.get("last_seen_at") or now,
    )
    db.add(entity)
    db.flush()
    identifiers = replace_identifiers(db, entity, payload.get("identifiers") or [])
    aliases = replace_aliases(db, entity, payload.get("aliases") or [])
    db.flush()
    snap = _entity_snapshot(entity, identifiers, aliases)
    record_data_change(
        db,
        entity_id=entity.id,
        change_type="create",
        before=None,
        after=snap,
        reason="dossier.entity.create",
    )
    record_audit(
        db,
        action="dossier.entity.create",
        target_id=entity.id,
        details={"entity_type": entity.entity_type, "canonical_name": entity.canonical_name},
    )
    return entity


def update_entity(db: Session, entity: Entity, payload: Dict[str, Any]) -> Entity:
    before_idents = load_identifiers(db, entity.id)
    before_aliases = load_aliases(db, entity.id)
    before = _entity_snapshot(entity, before_idents, before_aliases)

    if "canonical_name" in payload and payload["canonical_name"] is not None:
        name = str(payload["canonical_name"]).strip()
        if not name:
            raise ValueError("canonical_name cannot be empty")
        entity.canonical_name = name
        entity.normalized_name = normalize_text(name)
    simple_fields = (
        "entity_type",
        "description",
        "primary_location",
        "profile_data",
        "attributes_json",
        "source_first_id",
    )
    for field in simple_fields:
        if field in payload:
            setattr(entity, field, payload[field])
    if "profile_status" in payload and payload["profile_status"] is not None:
        ps = str(payload["profile_status"])
        entity.profile_status = ps if ps in PROFILE_STATUSES else entity.profile_status
    if "verification_status" in payload and payload["verification_status"] is not None:
        entity.verification_status = str(payload["verification_status"])
    if "confidence" in payload:
        entity.confidence = payload["confidence"]
    if "last_seen_at" in payload:
        entity.last_seen_at = payload["last_seen_at"]

    if "identifiers" in payload and payload["identifiers"] is not None:
        replace_identifiers(db, entity, payload["identifiers"] or [])
    if "aliases" in payload and payload["aliases"] is not None:
        replace_aliases(db, entity, payload["aliases"] or [])
    db.flush()
    after_idents = load_identifiers(db, entity.id)
    after_aliases = load_aliases(db, entity.id)
    after = _entity_snapshot(entity, after_idents, after_aliases)
    record_data_change(
        db,
        entity_id=entity.id,
        change_type="update",
        before=before,
        after=after,
        reason="dossier.entity.update",
    )
    record_audit(
        db,
        action="dossier.entity.update",
        target_id=entity.id,
        details={"entity_type": entity.entity_type, "canonical_name": entity.canonical_name},
    )
    return entity


def get_entity(db: Session, entity_id: str) -> Optional[Entity]:
    return db.get(Entity, entity_id)


@dataclass
class ListResult:
    items: List[Entity]
    total: int


def list_entities(
    db: Session,
    *,
    q: Optional[str] = None,
    entity_type: Optional[str] = None,
    profile_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    updated_from: Optional[datetime] = None,
    updated_to: Optional[datetime] = None,
    sort: str = "updated_desc",
    limit: int = 20,
    offset: int = 0,
) -> ListResult:
    stmt = select(Entity)
    count_stmt = select(func.count()).select_from(Entity)

    conditions = []
    if entity_type:
        conditions.append(Entity.entity_type == entity_type)
    if profile_status:
        conditions.append(Entity.profile_status == profile_status)
    if verification_status:
        conditions.append(Entity.verification_status == verification_status)
    if updated_from:
        conditions.append(Entity.updated_at >= updated_from)
    if updated_to:
        conditions.append(Entity.updated_at <= updated_to)
    if q:
        nq = normalize_text(q)
        ni = normalize_identifier(q)
        raw_q = q.strip()
        qcond = [
            Entity.normalized_name.like(f"%{nq}%"),
            Entity.canonical_name.like(f"%{raw_q}%"),
        ]
        alias_sub = select(EntityAlias.entity_id).where(
            EntityAlias.normalized_name.like(f"%{nq}%")
        )
        qcond.append(Entity.id.in_(alias_sub))
        if ni:
            ident_sub = select(EntityIdentifier.entity_id).where(
                or_(
                    EntityIdentifier.normalized_value.like(f"%{ni}%"),
                    EntityIdentifier.value.like(f"%{raw_q}%"),
                )
            )
            qcond.append(Entity.id.in_(ident_sub))
        conditions.append(or_(*qcond))

    if conditions:
        stmt = stmt.where(*conditions)
        count_stmt = count_stmt.where(*conditions)

    sort_map: Dict[str, Any] = {
        "updated_desc": Entity.updated_at.desc(),
        "updated_asc": Entity.updated_at.asc(),
        "created_desc": Entity.created_at.desc(),
        "created_asc": Entity.created_at.asc(),
        "name_asc": Entity.canonical_name.asc(),
    }
    order_col = sort_map.get(sort, Entity.updated_at.desc())
    stmt = stmt.order_by(order_col, Entity.id.asc())
    stmt = stmt.limit(limit).offset(offset)

    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.execute(stmt).scalars().all())
    return ListResult(items=items, total=total)


@dataclass
class DuplicateCandidateResult:
    entity: Entity
    score_level: str
    reasons: List[str]


def find_duplicate_candidates(
    db: Session, entity: Entity, limit: int = 10
) -> List[DuplicateCandidateResult]:
    identifiers = load_identifiers(db, entity.id)
    aliases = load_aliases(db, entity.id)
    norms = {entity.normalized_name} | {
        a.normalized_name for a in aliases if a.normalized_name
    }
    ident_norms = {i.normalized_value for i in identifiers if i.normalized_value}

    others = list(
        db.execute(select(Entity).where(Entity.id != entity.id)).scalars().all()
    )
    results: List[DuplicateCandidateResult] = []
    for other in others:
        o_idents = load_identifiers(db, other.id)
        o_aliases = load_aliases(db, other.id)
        reasons: List[str] = []
        strong = 0
        medium = 0

        if other.normalized_name and other.normalized_name in norms:
            reasons.append("nome_canonico_ou_alternativo_correspondente")
            strong += 1
        o_norms = {other.normalized_name} | {
            a.normalized_name for a in o_aliases if a.normalized_name
        }
        if norms & o_norms and "nome_canonico_ou_alternativo_correspondente" not in reasons:
            reasons.append("nome_alternativo_correspondente")
            strong += 1
        o_ident_norms = {i.normalized_value for i in o_idents if i.normalized_value}
        if ident_norms and o_ident_norms and (ident_norms & o_ident_norms):
            reasons.append("identificador_externo_correspondente")
            strong += 2

        same_type = entity.entity_type == other.entity_type
        if (
            not reasons
            and same_type
            and entity.normalized_name
            and other.normalized_name
            and len(entity.normalized_name) >= 8
            and entity.normalized_name[:12] == other.normalized_name[:12]
        ):
            reasons.append("nome_semelhante_mesmo_tipo")
            medium += 1

        if not reasons:
            continue
        if strong >= 2 or "identificador_externo_correspondente" in reasons:
            score = "high"
        elif strong == 1 or medium >= 1:
            score = "medium"
        else:
            score = "low"
        results.append(
            DuplicateCandidateResult(entity=other, score_level=score, reasons=reasons)
        )

    rank = {"high": 0, "medium": 1, "low": 2}
    results.sort(
        key=lambda r: (
            rank.get(r.score_level, 9),
            -(r.entity.updated_at.timestamp() if r.entity.updated_at else 0),
            r.entity.canonical_name or "",
        )
    )
    return results[:limit]
