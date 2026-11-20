from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.knowledge.dossiers.connections_taxonomy import SPECS, RelationTypeSpec
from app.knowledge.dossiers.research_service import record_audit, record_data_change
from app.knowledge.models.domain import Entity, Evidence, ExtractedClaim, Relationship

# D4 controlled vocabularies (operational)
DIRECTIONALITIES = {"directed", "undirected"}
NATURES = {"declarado", "observado", "inferido", "a_confirmar"}
VERIFICATION_STATUSES_D4 = {"nao_verificado", "verificado", "contestado"}
# Global legacy values tolerated defensively on read/normalize
VERIFICATION_STATUSES_LEGACY_TOLERATED = {
    "nao_verificado",
    "em_verificacao",
    "verificado",
    "contestado",
    "invalido",
}
CONNECTION_STATUSES = {"active", "needs_review", "inactive", "archived"}
TIME_PRECISIONS = {"exact", "month", "year", "estimated", "unknown"}
CONSIDERED_FOR_CONFLICT = {"active", "needs_review", "inactive"}
CREATED_BY_RE = re.compile(r"^(human_user|ai_agent|internal_process):[A-Za-z0-9._-]{1,80}$")


class D4ValidationError(ValueError):
    code = 422


class D4NotFoundError(ValueError):
    code = 404


class D4ConflictError(ValueError):
    code = 409


@dataclass
class ListConnectionsResult:
    items: List[Relationship]
    total: int


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def ensure_entity(db: Session, entity_id: str) -> Entity:
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise D4NotFoundError("entity not found")
    return entity


def _get_claim(db: Session, claim_id: str) -> ExtractedClaim:
    claim = db.get(ExtractedClaim, claim_id)
    if claim is None:
        raise D4NotFoundError("claim not found")
    return claim


def _get_evidence(db: Session, evidence_id: str) -> Evidence:
    ev = db.get(Evidence, evidence_id)
    if ev is None:
        raise D4NotFoundError("evidence not found")
    return ev


def get_connection(db: Session, connection_id: str) -> Optional[Relationship]:
    return db.get(Relationship, connection_id)


def spec_for(relation_type: str) -> RelationTypeSpec:
    spec = SPECS.get(relation_type)
    if spec is None:
        raise D4ValidationError("relation_type does not exist in taxonomy")
    if spec.status_mvp != "approved":
        raise D4ValidationError("relation_type is not operationally approved for MVP")
    return spec


def _normalize_directionality(spec: RelationTypeSpec, provided: Optional[str]) -> str:
    if provided is None or str(provided).strip() == "":
        return spec.directionality
    v = str(provided).strip()
    if v not in DIRECTIONALITIES:
        raise D4ValidationError("invalid directionality")
    if v != spec.directionality:
        raise D4ValidationError("directionality is incompatible with relation_type taxonomy")
    return v


def _normalize_nature(value: Optional[str], default: str = "declarado") -> str:
    v = str(value or default).strip()
    if v not in NATURES:
        raise D4ValidationError("invalid nature")
    return v


def _normalize_verification(value: Optional[str], default: str = "nao_verificado") -> str:
    v = str(value or default).strip()
    if v not in VERIFICATION_STATUSES_D4:
        # D4 operational writes must use D4 subset
        raise D4ValidationError("invalid verification_status")
    return v


def _normalize_status(value: Optional[str], default: str = "active") -> str:
    v = str(value or default).strip()
    if v not in CONNECTION_STATUSES:
        raise D4ValidationError("invalid status")
    return v


def _normalize_time_precision(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip()
    if not v:
        return None
    if v not in TIME_PRECISIONS:
        raise D4ValidationError("invalid time_precision")
    return v


def _normalize_confidence(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        c = float(value)
    except Exception as exc:  # noqa: BLE001
        raise D4ValidationError("invalid confidence") from exc
    if c < 0.0 or c > 1.0:
        raise D4ValidationError("confidence must be between 0 and 1")
    return c


def _validate_temporal(valid_from: Optional[datetime], valid_to: Optional[datetime]) -> None:
    if valid_from is not None and valid_to is not None and valid_to < valid_from:
        raise D4ValidationError("valid_to must be greater than or equal to valid_from")


def _validate_created_by(value: Optional[str], *, required: bool) -> Optional[str]:
    if value is None or str(value).strip() == "":
        if required:
            raise D4ValidationError("created_by is required for new D4 records")
        return None
    v = str(value).strip()
    if not CREATED_BY_RE.match(v):
        if required:
            raise D4ValidationError("created_by must follow controlled format")
        # legacy/compat in reads; not used for creation
        return v
    return v


def _validate_anti_promotion(nature: str, verification_status: str) -> None:
    if nature == "inferido" and verification_status == "verificado":
        raise D4ValidationError(
            "inferido cannot be promoted to verificado without explicit nature reclassification"
        )


def _canonical_undirected(a: str, b: str) -> Tuple[str, str]:
    return (a, b) if a <= b else (b, a)


def _validate_entity_type_compatibility(
    spec: RelationTypeSpec, from_entity: Entity, to_entity: Entity
) -> None:
    # effective semantic compatibility: entity types must be in allowed sets
    if from_entity.entity_type not in spec.from_entity_types:
        raise D4ValidationError("from entity type not allowed for relation_type")
    if to_entity.entity_type not in spec.to_entity_types:
        raise D4ValidationError("to entity type not allowed for relation_type")


def _resolve_endpoints(
    spec: RelationTypeSpec,
    anchor_entity_id: str,
    payload: Dict[str, Any],
    db: Session,
) -> Tuple[Entity, Entity]:
    """Resolve and validate from/to entities for create (and for updates changing endpoints/type)."""
    from_id = payload.get("from_entity_id")
    to_id = payload.get("to_entity_id")
    other_id = payload.get("other_entity_id")

    if spec.directionality == "undirected":
        if from_id or to_id:
            # if explicitly provided, both must be present and form an undirected pair with anchor/other or be coherent
            if not (from_id and to_id):
                raise D4ValidationError("undirected relation requires both endpoints when specified")
            a, b = str(from_id), str(to_id)
            if anchor_entity_id not in {a, b}:
                raise D4ValidationError("anchor entity must be one of the endpoints")
            if other_id and str(other_id) not in {a, b}:
                raise D4ValidationError("other_entity_id inconsistent with endpoints")
            # normalize to canonical regardless of input order
            ca, cb = _canonical_undirected(a, b)
            from_entity = ensure_entity(db, ca)
            to_entity = ensure_entity(db, cb)
        else:
            if not other_id:
                raise D4ValidationError("other_entity_id is required")
            a, b = _canonical_undirected(anchor_entity_id, str(other_id))
            from_entity = ensure_entity(db, a)
            to_entity = ensure_entity(db, b)
    else:
        # directed: require explicit, unambiguous endpoints OR (other_entity_id + perspective) - prefer explicit
        if from_id and to_id:
            a, b = str(from_id), str(to_id)
            if anchor_entity_id not in {a, b}:
                raise D4ValidationError("anchor entity must be one of the endpoints")
            from_entity = ensure_entity(db, a)
            to_entity = ensure_entity(db, b)
        elif other_id and (payload.get("anchor_role") or payload.get("perspective")):
            role = str(payload.get("anchor_role") or payload.get("perspective") or "").strip().lower()
            other = str(other_id)
            if role in {"from", "source", "origin"}:
                from_entity = ensure_entity(db, anchor_entity_id)
                to_entity = ensure_entity(db, other)
            elif role in {"to", "target", "destination"}:
                from_entity = ensure_entity(db, other)
                to_entity = ensure_entity(db, anchor_entity_id)
            else:
                raise D4ValidationError("directed relation requires explicit from_entity_id and to_entity_id")
        else:
            raise D4ValidationError("directed relation requires explicit from_entity_id and to_entity_id")

    if from_entity.id == to_entity.id:
        raise D4ValidationError("self-relation is not allowed in MVP")
    _validate_entity_type_compatibility(spec, from_entity, to_entity)
    return from_entity, to_entity


def _to_utc_naive(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        try:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            return dt.replace(tzinfo=None)
    return dt


def _intervals_conflict(
    s1: Optional[datetime],
    e1: Optional[datetime],
    s2: Optional[datetime],
    e2: Optional[datetime],
) -> Tuple[bool, str]:
    """Return (is_conflict, reason). Conservative per plan."""
    a1s, a1e = _to_utc_naive(s1), _to_utc_naive(e1)
    a2s, a2e = _to_utc_naive(s2), _to_utc_naive(e2)
    # Equivalent
    if a1s == a2s and a1e == a2e:
        return True, "equivalent_period"
    # Disjoint (strict, clearly separated)
    if a1e is not None and a2s is not None and a1e < a2s:
        return False, "disjoint"
    if a2e is not None and a1s is not None and a2e < a1s:
        return False, "disjoint"
    # Not safely disjoint/equivalent (overlap, touching, or incomparable due to unknowns)
    return True, "overlap_or_ambiguous"


def _semantic_forms(spec: RelationTypeSpec, from_id: str, to_id: str) -> List[Tuple[str, str, str]]:
    """Return list of (relation_type, from_id, to_id) forms representing same semantic link."""
    if spec.directionality == "undirected":
        a, b = _canonical_undirected(from_id, to_id)
        return [(spec.id, a, b)]
    forms = [(spec.id, from_id, to_id)]
    inv = spec.inverse_type_id
    if inv:
        forms.append((inv, to_id, from_id))
    return forms


def _check_semantic_conflicts(
    db: Session,
    *,
    spec: RelationTypeSpec,
    from_id: str,
    to_id: str,
    valid_from: Optional[datetime],
    valid_to: Optional[datetime],
    exclude_id: Optional[str] = None,
) -> None:
    forms = _semantic_forms(spec, from_id, to_id)
    # considered statuses
    status_filter = list(CONSIDERED_FOR_CONFLICT)
    # Build OR conditions for all forms
    conds = []
    for rtype, f, t in forms:
        if SPECS.get(rtype, spec).directionality == "undirected":
            a, b = _canonical_undirected(f, t)
            conds.append(and_(Relationship.relation_type == rtype, Relationship.from_entity_id == a, Relationship.to_entity_id == b))
        else:
            conds.append(and_(Relationship.relation_type == rtype, Relationship.from_entity_id == f, Relationship.to_entity_id == t))
    if not conds:
        return
    stmt = select(Relationship).where(Relationship.status.in_(status_filter)).where(or_(*conds))
    if exclude_id:
        stmt = stmt.where(Relationship.id != exclude_id)
    # lock-ish not available portably in sqlite the same way, but transactional check is required
    existing = list(db.execute(stmt).scalars().all())
    for rel in existing:
        conflict, _reason = _intervals_conflict(valid_from, valid_to, rel.valid_from, rel.valid_to)
        if conflict:
            raise D4ConflictError("semantic duplicate or temporal conflict with existing relationship")


def _validate_claim_evidence(
    db: Session, claim_id: Optional[str], evidence_id: Optional[str]
) -> Tuple[Optional[ExtractedClaim], Optional[Evidence]]:
    claim = _get_claim(db, claim_id) if claim_id else None
    evidence = _get_evidence(db, evidence_id) if evidence_id else None
    if claim and evidence and evidence.claim_id and evidence.claim_id != claim.id:
        raise D4ValidationError("evidence does not belong to claim")
    return claim, evidence


def _snapshot(obj: Relationship) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "from_entity_id": obj.from_entity_id,
        "to_entity_id": obj.to_entity_id,
        "relation_type": obj.relation_type,
        "directionality": obj.directionality,
        "attributes_json": obj.attributes_json,
        "claim_id": obj.claim_id,
        "evidence_id": obj.evidence_id,
        "confidence": obj.confidence,
        "nature": obj.nature,
        "verification_status": obj.verification_status,
        "status": obj.status,
        "description": obj.description,
        "justification": obj.justification,
        "source_locator": obj.source_locator,
        "occurred_at": obj.occurred_at.isoformat() if obj.occurred_at else None,
        "valid_from": obj.valid_from.isoformat() if obj.valid_from else None,
        "valid_to": obj.valid_to.isoformat() if obj.valid_to else None,
        "time_precision": obj.time_precision,
        "created_by": obj.created_by,
    }


def _effective_created_by_for_new(payload: Dict[str, Any]) -> str:
    return _validate_created_by(payload.get("created_by"), required=True)  # type: ignore[return-value]


def create_connection(
    db: Session, anchor_entity_id: str, payload: Dict[str, Any], *, actor: Optional[str] = "local"
) -> Relationship:
    ensure_entity(db, anchor_entity_id)
    relation_type = str(payload.get("relation_type") or "").strip()
    if not relation_type:
        raise D4ValidationError("relation_type is required")
    spec = spec_for(relation_type)
    directionality = _normalize_directionality(spec, payload.get("directionality"))
    from_entity, to_entity = _resolve_endpoints(spec, anchor_entity_id, payload, db)

    nature = _normalize_nature(payload.get("nature"), "declarado")
    verification_status = _normalize_verification(payload.get("verification_status"), "nao_verificado")
    status = _normalize_status(payload.get("status"), "active")
    _validate_anti_promotion(nature, verification_status)

    occurred_at = payload.get("occurred_at")
    valid_from = payload.get("valid_from")
    valid_to = payload.get("valid_to")
    _validate_temporal(valid_from, valid_to)
    time_precision = _normalize_time_precision(payload.get("time_precision"))
    confidence = _normalize_confidence(payload.get("confidence"))

    claim_id = payload.get("claim_id") or None
    evidence_id = payload.get("evidence_id") or None
    _validate_claim_evidence(db, claim_id, evidence_id)

    created_by = _effective_created_by_for_new(payload)

    # Deterministic, transactional semantic/temporal conflict check
    _check_semantic_conflicts(
        db,
        spec=spec,
        from_id=from_entity.id,
        to_id=to_entity.id,
        valid_from=valid_from,
        valid_to=valid_to,
        exclude_id=None,
    )

    obj = Relationship(
        from_entity_id=from_entity.id,
        to_entity_id=to_entity.id,
        relation_type=relation_type,
        directionality=directionality,
        attributes_json=payload.get("attributes_json"),
        claim_id=claim_id,
        evidence_id=evidence_id,
        confidence=confidence,
        nature=nature,
        verification_status=verification_status,
        status=status,
        description=(str(payload["description"]).strip() if payload.get("description") else None),
        justification=payload.get("justification"),
        source_locator=payload.get("source_locator"),
        occurred_at=occurred_at,
        valid_from=valid_from,
        valid_to=valid_to,
        time_precision=time_precision,
        created_by=created_by,
    )
    db.add(obj)
    db.flush()
    record_data_change(
        db,
        entity_table="relationships",
        entity_id=obj.id,
        change_type="create",
        before=None,
        after=_jsonable(_snapshot(obj)),
        reason="dossier.connection.create",
        actor=actor,
    )
    record_audit(
        db,
        action="dossier.connection.create",
        target_type="relationship",
        target_id=obj.id,
        details={
            "from_entity_id": obj.from_entity_id,
            "to_entity_id": obj.to_entity_id,
            "relation_type": obj.relation_type,
            "nature": obj.nature,
            "status": obj.status,
        },
        actor_id=actor,
    )
    return obj


def _ensure_updatable_not_archived_reactivation(before_status: str, new_status: Optional[str]) -> None:
    if before_status == "archived" and new_status is not None and new_status != "archived":
        raise D4ValidationError("archived relationships cannot be reactivated directly")


def update_connection(
    db: Session, obj: Relationship, payload: Dict[str, Any], *, actor: Optional[str] = "local"
) -> Relationship:
    before = _jsonable(_snapshot(obj))

    # Determine target spec/type
    relation_type = obj.relation_type
    if "relation_type" in payload and payload["relation_type"] is not None:
        relation_type = str(payload["relation_type"]).strip()
    spec = spec_for(relation_type)

    # Resolve endpoints if relevant fields present
    endpoints_changing = any(k in payload for k in ("from_entity_id", "to_entity_id", "other_entity_id", "anchor_role", "perspective"))
    type_changing = relation_type != obj.relation_type
    if endpoints_changing or type_changing:
        # resolve using anchor = from side of existing? easier: require explicit from/to for updates that change endpoints/type
        # Build effective payload; ensure anchor presence not required beyond explicitness
        eff = dict(payload)
        eff.setdefault("from_entity_id", obj.from_entity_id)
        eff.setdefault("to_entity_id", obj.to_entity_id)
        # if still ambiguous for directed and not explicit, require explicit
        if spec.directionality == "directed":
            # need explicit from/to after change
            from_id = str(eff.get("from_entity_id") or obj.from_entity_id)
            to_id = str(eff.get("to_entity_id") or obj.to_entity_id)
            from_entity = ensure_entity(db, from_id)
            to_entity = ensure_entity(db, to_id)
        else:
            a = str(eff.get("from_entity_id") or obj.from_entity_id)
            b = str(eff.get("to_entity_id") or obj.to_entity_id)
            ca, cb = _canonical_undirected(a, b)
            from_entity = ensure_entity(db, ca)
            to_entity = ensure_entity(db, cb)
        if from_entity.id == to_entity.id:
            raise D4ValidationError("self-relation is not allowed in MVP")
        _validate_entity_type_compatibility(spec, from_entity, to_entity)
        new_from, new_to = from_entity.id, to_entity.id
    else:
        new_from, new_to = obj.from_entity_id, obj.to_entity_id

    directionality = obj.directionality
    if "directionality" in payload or type_changing:
        directionality = _normalize_directionality(spec, payload.get("directionality", spec.directionality))

    nature = obj.nature if ("nature" not in payload or payload.get("nature") is None) else _normalize_nature(payload.get("nature"), obj.nature or "declarado")
    verification_status = (
        obj.verification_status
        if ("verification_status" not in payload or payload.get("verification_status") is None)
        else _normalize_verification(payload.get("verification_status"), obj.verification_status or "nao_verificado")
    )
    status = obj.status if ("status" not in payload or payload.get("status") is None) else _normalize_status(payload.get("status"), obj.status or "active")
    _ensure_updatable_not_archived_reactivation(obj.status or "active", status)
    _validate_anti_promotion(nature, verification_status)

    valid_from = obj.valid_from
    valid_to = obj.valid_to
    if "valid_from" in payload:
        valid_from = payload.get("valid_from")
    if "valid_to" in payload:
        valid_to = payload.get("valid_to")
    occurred_at = obj.occurred_at
    if "occurred_at" in payload:
        occurred_at = payload.get("occurred_at")
    _validate_temporal(valid_from, valid_to)

    time_precision = obj.time_precision
    if "time_precision" in payload:
        time_precision = _normalize_time_precision(payload.get("time_precision"))

    confidence = obj.confidence
    if "confidence" in payload:
        confidence = _normalize_confidence(payload.get("confidence"))

    claim_id = obj.claim_id
    evidence_id = obj.evidence_id
    if "claim_id" in payload:
        claim_id = payload.get("claim_id") or None
    if "evidence_id" in payload:
        evidence_id = payload.get("evidence_id") or None
    _validate_claim_evidence(db, claim_id, evidence_id)

    # Revalidate semantic/temporal conflicts if key/vigencia relevant fields change or status becomes considered
    relevant_change = type_changing or endpoints_changing or ("valid_from" in payload) or ("valid_to" in payload) or ("status" in payload)
    if relevant_change and status in CONSIDERED_FOR_CONFLICT:
        _check_semantic_conflicts(
            db,
            spec=spec,
            from_id=new_from,
            to_id=new_to,
            valid_from=valid_from,
            valid_to=valid_to,
            exclude_id=obj.id,
        )

    # Apply
    obj.relation_type = relation_type
    obj.directionality = directionality
    obj.from_entity_id = new_from
    obj.to_entity_id = new_to
    obj.nature = nature
    obj.verification_status = verification_status
    obj.status = status
    obj.valid_from = valid_from
    obj.valid_to = valid_to
    obj.occurred_at = occurred_at
    obj.time_precision = time_precision
    obj.confidence = confidence
    obj.claim_id = claim_id
    obj.evidence_id = evidence_id
    if "description" in payload:
        obj.description = (str(payload["description"]).strip() if payload.get("description") else None)
    if "justification" in payload:
        obj.justification = payload.get("justification")
    if "source_locator" in payload:
        obj.source_locator = payload.get("source_locator")
    if "attributes_json" in payload:
        obj.attributes_json = payload.get("attributes_json")

    db.flush()
    record_data_change(
        db,
        entity_table="relationships",
        entity_id=obj.id,
        change_type="update",
        before=before,
        after=_jsonable(_snapshot(obj)),
        reason="dossier.connection.update",
        actor=actor,
    )
    record_audit(
        db,
        action="dossier.connection.update",
        target_type="relationship",
        target_id=obj.id,
        details={
            "from_entity_id": obj.from_entity_id,
            "to_entity_id": obj.to_entity_id,
            "relation_type": obj.relation_type,
            "nature": obj.nature,
            "status": obj.status,
        },
        actor_id=actor,
    )
    return obj


def list_connections_for_entity(
    db: Session,
    entity_id: str,
    *,
    direction: Optional[str] = None,  # incoming|outgoing|both
    relation_type: Optional[str] = None,
    category: Optional[str] = None,
    nature: Optional[str] = None,
    verification_status: Optional[str] = None,
    status: Optional[str] = None,
    occurred_from: Optional[datetime] = None,
    occurred_to: Optional[datetime] = None,
    valid_from: Optional[datetime] = None,
    valid_to: Optional[datetime] = None,
    has_evidence: Optional[bool] = None,
    q: Optional[str] = None,
    sort: str = "updated_desc",
    limit: int = 20,
    offset: int = 0,
) -> ListConnectionsResult:
    # base: relationships where entity is either endpoint
    cond = or_(Relationship.from_entity_id == entity_id, Relationship.to_entity_id == entity_id)
    stmt = select(Relationship).where(cond)
    count_stmt = select(func.count()).select_from(Relationship).where(cond)

    filters = []
    if direction == "outgoing":
        filters.append(Relationship.from_entity_id == entity_id)
    elif direction == "incoming":
        filters.append(Relationship.to_entity_id == entity_id)
    # both/default -> either endpoint
    if relation_type:
        filters.append(Relationship.relation_type == relation_type)
    if nature:
        filters.append(Relationship.nature == nature)
    if verification_status:
        filters.append(Relationship.verification_status == verification_status)
    if status:
        filters.append(Relationship.status == status)
    if occurred_from:
        filters.append(Relationship.occurred_at.is_not(None))
        filters.append(Relationship.occurred_at >= occurred_from)
    if occurred_to:
        filters.append(Relationship.occurred_at.is_not(None))
        filters.append(Relationship.occurred_at <= occurred_to)
    if valid_from:
        filters.append(Relationship.valid_from.is_not(None))
        filters.append(Relationship.valid_from >= valid_from)
    if valid_to:
        filters.append(Relationship.valid_to.is_not(None))
        filters.append(Relationship.valid_to <= valid_to)
    if has_evidence is True:
        filters.append(or_(Relationship.claim_id.is_not(None), Relationship.evidence_id.is_not(None), Relationship.source_locator.is_not(None)))
    elif has_evidence is False:
        filters.append(Relationship.claim_id.is_(None))
        filters.append(Relationship.evidence_id.is_(None))
        filters.append(or_(Relationship.source_locator.is_(None), Relationship.source_locator == ""))
    if category:
        # filter by taxonomy category
        type_ids = [tid for tid, s in SPECS.items() if s.category == category]
        if type_ids:
            filters.append(Relationship.relation_type.in_(type_ids))
        else:
            filters.append(Relationship.relation_type == "__none__")
    if q:
        like = f"%{q.strip()}%"
        filters.append(
            or_(
                Relationship.relation_type.like(like),
                Relationship.description.like(like),
                Relationship.justification.like(like),
                Relationship.source_locator.like(like),
            )
        )

    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    sort_map = {
        "updated_desc": [Relationship.updated_at.desc(), Relationship.id.asc()],
        "updated_asc": [Relationship.updated_at.asc(), Relationship.id.asc()],
        "occurred_desc": [Relationship.occurred_at.desc(), Relationship.updated_at.desc(), Relationship.id.asc()],
        "occurred_asc": [Relationship.occurred_at.asc(), Relationship.updated_at.desc(), Relationship.id.asc()],
        "created_desc": [Relationship.created_at.desc(), Relationship.id.asc()],
        "created_asc": [Relationship.created_at.asc(), Relationship.id.asc()],
    }
    stmt = stmt.order_by(*sort_map.get(sort, sort_map["updated_desc"]))
    stmt = stmt.limit(limit).offset(offset)
    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.execute(stmt).scalars().all())
    return ListConnectionsResult(items=items, total=total)


def connections_summary(db: Session, entity_id: str) -> Dict[str, Any]:
    ensure_entity(db, entity_id)
    base_filter = or_(Relationship.from_entity_id == entity_id, Relationship.to_entity_id == entity_id)
    total = int(
        db.execute(select(func.count()).select_from(Relationship).where(base_filter)).scalar_one() or 0
    )

    def counts(col: Any) -> Dict[str, int]:
        rows = db.execute(select(col, func.count()).where(base_filter).group_by(col)).all()
        return {str(k): int(v) for k, v in rows if k is not None}

    by_type = counts(Relationship.relation_type)
    by_category: Dict[str, int] = {}
    for tid, c in by_type.items():
        cat = SPECS[tid].category if tid in SPECS else "Desconhecida"
        by_category[cat] = by_category.get(cat, 0) + c

    outgoing = int(
        db.execute(
            select(func.count()).select_from(Relationship).where(Relationship.from_entity_id == entity_id)
        ).scalar_one()
        or 0
    )
    incoming = int(
        db.execute(
            select(func.count()).select_from(Relationship).where(Relationship.to_entity_id == entity_id)
        ).scalar_one()
        or 0
    )
    # undirected canonical stored as from=min,to=max so entity can appear on either side; both count as either in some sense
    # but easier report outgoing/incoming by stored orientation plus undirected count
    undirected_count = int(
        db.execute(
            select(func.count())
            .select_from(Relationship)
            .where(base_filter, Relationship.directionality == "undirected")
        ).scalar_one()
        or 0
    )
    with_evidence = int(
        db.execute(
            select(func.count())
            .select_from(Relationship)
            .where(
                base_filter,
                or_(
                    Relationship.claim_id.is_not(None),
                    Relationship.evidence_id.is_not(None),
                    and_(Relationship.source_locator.is_not(None), Relationship.source_locator != ""),
                ),
            )
        ).scalar_one()
        or 0
    )

    return {
        "entity_id": entity_id,
        "connections_count": total,
        "by_nature": counts(Relationship.nature),
        "by_verification_status": counts(Relationship.verification_status),
        "by_status": counts(Relationship.status),
        "by_type": by_type,
        "by_category": by_category,
        "outgoing_count": outgoing,
        "incoming_count": incoming,
        "undirected_count": undirected_count,
        "with_evidence_count": with_evidence,
    }
