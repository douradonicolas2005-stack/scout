from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.knowledge.models.domain import (
    AuditEvent,
    ClaimConflict,
    ClaimEntityLink,
    DataChange,
    Document,
    DocumentEntityLink,
    Entity,
    Evidence,
    ExtractedClaim,
    ProcessingEvent,
    ResearchSource,
)
from app.knowledge.provenance import ClaimType, VerificationStatus

RELIABILITY_STATUSES = {"nao_avaliada", "baixa", "media", "alta", "contestada"}
VERIFICATION_STATUSES = {v.value for v in VerificationStatus}
CLAIM_TYPES = {v.value for v in ClaimType}
EVIDENCE_RELATION_TYPES = {"supports", "contests", "contextualizes"}
CONFLICT_STATUSES = {"open", "under_review", "resolved", "dismissed"}
CLAIM_CONFLICT_STATES = {"none", "contested", "conflicting", "under_review"}
CLAIM_ORIGINS = {"manual", "deterministic_import", "assisted"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def record_audit(
    db: Session,
    *,
    action: str,
    target_type: str,
    target_id: Optional[str] = None,
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
    entity_table: str,
    entity_id: str,
    change_type: str,
    before: Optional[Dict[str, Any]],
    after: Optional[Dict[str, Any]],
    reason: Optional[str] = None,
    actor: Optional[str] = "local",
) -> None:
    db.add(
        DataChange(
            entity_table=entity_table,
            entity_id=entity_id,
            change_type=change_type,
            before_json=before,
            after_json=after,
            reason=reason,
            actor=actor,
        )
    )


def record_processing_event(
    db: Session,
    *,
    stage: str,
    status: str,
    message: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    db.add(
        ProcessingEvent(
            stage=stage,
            status=status,
            message=message,
            payload_json=payload or {},
        )
    )


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
        raise ValueError("entity not found")
    return entity


# ---------------- Research Sources ----------------


def _research_source_snapshot(obj: ResearchSource) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "name": obj.name,
        "source_type": obj.source_type,
        "domain": obj.domain,
        "url": obj.url,
        "description": obj.description,
        "classification": obj.classification,
        "consulted_at": obj.consulted_at.isoformat() if obj.consulted_at else None,
        "last_verified_at": obj.last_verified_at.isoformat() if obj.last_verified_at else None,
        "reliability_status": obj.reliability_status,
        "reliability_justification": obj.reliability_justification,
        "verification_status": obj.verification_status,
        "ingestion_source_id": obj.ingestion_source_id,
        "metadata_json": obj.metadata_json,
        "created_by": obj.created_by,
    }


def create_research_source(db: Session, payload: Dict[str, Any]) -> ResearchSource:
    name = str(payload.get("name") or "").strip()
    source_type = str(payload.get("source_type") or "").strip()
    if not name:
        raise ValueError("name is required")
    if not source_type:
        raise ValueError("source_type is required")
    rs = ResearchSource(
        name=name,
        source_type=source_type,
        domain=(str(payload["domain"]).strip() if payload.get("domain") else None),
        url=payload.get("url"),
        description=payload.get("description"),
        classification=(
            str(payload["classification"]).strip() if payload.get("classification") else None
        ),
        consulted_at=payload.get("consulted_at"),
        last_verified_at=payload.get("last_verified_at"),
        reliability_status=(
            str(payload.get("reliability_status") or "nao_avaliada")
            if str(payload.get("reliability_status") or "nao_avaliada") in RELIABILITY_STATUSES
            else "nao_avaliada"
        ),
        reliability_justification=payload.get("reliability_justification"),
        verification_status=(
            str(payload.get("verification_status") or "nao_verificado")
            if str(payload.get("verification_status") or "nao_verificado") in VERIFICATION_STATUSES
            else "nao_verificado"
        ),
        ingestion_source_id=payload.get("ingestion_source_id"),
        metadata_json=payload.get("metadata_json"),
        created_by=payload.get("created_by") or "local",
    )
    db.add(rs)
    db.flush()
    record_data_change(
        db,
        entity_table="research_sources",
        entity_id=rs.id,
        change_type="create",
        before=None,
        after=_jsonable(_research_source_snapshot(rs)),
        reason="dossier.research_source.create",
    )
    record_audit(
        db,
        action="dossier.research_source.create",
        target_type="research_source",
        target_id=rs.id,
        details={"name": rs.name, "source_type": rs.source_type},
    )
    return rs


def get_research_source(db: Session, source_id: str) -> Optional[ResearchSource]:
    return db.get(ResearchSource, source_id)


@dataclass
class ListResearchSourcesResult:
    items: List[ResearchSource]
    total: int


def list_research_sources(
    db: Session,
    *,
    q: Optional[str] = None,
    source_type: Optional[str] = None,
    classification: Optional[str] = None,
    reliability_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    sort: str = "updated_desc",
    limit: int = 20,
    offset: int = 0,
) -> ListResearchSourcesResult:
    stmt = select(ResearchSource)
    count_stmt = select(func.count()).select_from(ResearchSource)
    conds = []
    if source_type:
        conds.append(ResearchSource.source_type == source_type)
    if classification:
        conds.append(ResearchSource.classification == classification)
    if reliability_status:
        conds.append(ResearchSource.reliability_status == reliability_status)
    if verification_status:
        conds.append(ResearchSource.verification_status == verification_status)
    if q:
        raw = q.strip()
        like = f"%{raw}%"
        conds.append(
            or_(
                ResearchSource.name.like(like),
                ResearchSource.domain.like(like),
                ResearchSource.url.like(like),
                ResearchSource.description.like(like),
            )
        )
    if conds:
        stmt = stmt.where(*conds)
        count_stmt = count_stmt.where(*conds)
    sort_map = {
        "updated_desc": ResearchSource.updated_at.desc(),
        "updated_asc": ResearchSource.updated_at.asc(),
        "name_asc": ResearchSource.name.asc(),
        "consulted_desc": ResearchSource.consulted_at.desc(),
        "verified_desc": ResearchSource.last_verified_at.desc(),
    }
    stmt = stmt.order_by(
        sort_map.get(sort, ResearchSource.updated_at.desc()), ResearchSource.id.asc()
    )
    stmt = stmt.limit(limit).offset(offset)
    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.execute(stmt).scalars().all())
    return ListResearchSourcesResult(items=items, total=total)


def update_research_source(
    db: Session, rs: ResearchSource, payload: Dict[str, Any]
) -> ResearchSource:
    before = _jsonable(_research_source_snapshot(rs))
    for field in [
        "name",
        "source_type",
        "domain",
        "url",
        "description",
        "classification",
        "consulted_at",
        "last_verified_at",
        "reliability_justification",
        "ingestion_source_id",
        "metadata_json",
    ]:
        if field in payload:
            val = payload[field]
            if field in {"name", "source_type"} and val is not None:
                sval = str(val).strip()
                if not sval:
                    raise ValueError(f"{field} cannot be empty")
                setattr(rs, field, sval)
            elif field in {"domain", "classification"} and val is not None:
                setattr(rs, field, str(val).strip() or None)
            else:
                setattr(rs, field, val)
    if "reliability_status" in payload and payload["reliability_status"] is not None:
        v = str(payload["reliability_status"])
        rs.reliability_status = v if v in RELIABILITY_STATUSES else rs.reliability_status
    if "verification_status" in payload and payload["verification_status"] is not None:
        v = str(payload["verification_status"])
        rs.verification_status = v if v in VERIFICATION_STATUSES else rs.verification_status
    db.flush()
    after = _jsonable(_research_source_snapshot(rs))
    record_data_change(
        db,
        entity_table="research_sources",
        entity_id=rs.id,
        change_type="update",
        before=before,
        after=after,
        reason="dossier.research_source.update",
    )
    record_audit(
        db,
        action="dossier.research_source.update",
        target_type="research_source",
        target_id=rs.id,
        details={"name": rs.name},
    )
    return rs


# ---------------- Documents ----------------


def _document_snapshot(doc: Document, entity_links: Sequence[DocumentEntityLink]) -> Dict[str, Any]:
    return {
        "id": doc.id,
        "title": doc.title,
        "document_type": doc.document_type,
        "description": doc.description,
        "origin_type": doc.origin_type,
        "source_locator": doc.source_locator,
        "mime_type": doc.mime_type,
        "storage_path": doc.storage_path,
        "checksum": doc.checksum,
        "content_hash": doc.content_hash,
        "size_bytes": doc.size_bytes,
        "language": doc.language,
        "published_at": doc.published_at.isoformat() if doc.published_at else None,
        "occurred_at": doc.occurred_at.isoformat() if doc.occurred_at else None,
        "captured_at": doc.captured_at.isoformat() if doc.captured_at else None,
        "collected_at": doc.collected_at.isoformat() if doc.collected_at else None,
        "verification_status": doc.verification_status,
        "access_level": doc.access_level,
        "license_terms": doc.license_terms,
        "is_reference_only": doc.is_reference_only,
        "metadata_json": doc.metadata_json,
        "source_id": doc.source_id,
        "raw_record_id": doc.raw_record_id,
        "research_source_id": doc.research_source_id,
        "entity_links": [
            {"entity_id": link.entity_id, "role": link.role, "notes": link.notes}
            for link in entity_links
        ],
    }


def _ensure_document_anchor(payload: Dict[str, Any]) -> None:
    if (
        payload.get("source_id")
        or payload.get("raw_record_id")
        or payload.get("research_source_id")
        or payload.get("source_locator")
    ):
        return
    raise ValueError(
        "document must have at least one provenance anchor "
        "(source_id, raw_record_id, research_source_id, or source_locator)"
    )


def _validate_storage_path(storage_path: Optional[str], is_reference_only: bool) -> Optional[str]:
    if storage_path is None:
        return None
    sp = str(storage_path).strip()
    if not sp:
        return None
    if is_reference_only:
        return sp
    # allow only paths under documents_dir (relative or absolute inside)
    try:
        base = settings.documents_dir.resolve()
        p = Path(sp)
        resolved = p.resolve() if p.is_absolute() else (base / p).resolve()
        if base == resolved or base in resolved.parents:
            return str(resolved)
    except Exception:
        pass
    # if outside, keep as metadata reference but do not treat as managed copy
    return sp


def _compute_hash_for_path(storage_path: Optional[str]) -> Tuple[Optional[str], Optional[int]]:
    if not storage_path:
        return None, None
    try:
        p = Path(storage_path)
        if not p.exists() or not p.is_file():
            return None, None
        data = p.read_bytes()
        return hashlib.sha256(data).hexdigest(), len(data)
    except Exception:
        return None, None


def load_document_links(db: Session, document_id: str) -> List[DocumentEntityLink]:
    stmt = select(DocumentEntityLink).where(DocumentEntityLink.document_id == document_id)
    return list(db.execute(stmt).scalars().all())


def sync_document_entity_links(
    db: Session, doc: Document, links: Iterable[Dict[str, Any]]
) -> List[DocumentEntityLink]:
    # replace strategy for deterministic state
    db.query(DocumentEntityLink).filter(DocumentEntityLink.document_id == doc.id).delete(
        synchronize_session=False
    )
    out: List[DocumentEntityLink] = []
    seen = set()
    for item in links:
        eid = str(item.get("entity_id") or "").strip()
        if not eid:
            continue
        role = item.get("role")
        role_norm = str(role).strip() if role is not None and str(role).strip() else None
        key = (eid, role_norm or "")
        if key in seen:
            continue
        if db.get(Entity, eid) is None:
            raise ValueError(f"linked entity not found: {eid}")
        seen.add(key)
        link = DocumentEntityLink(
            document_id=doc.id,
            entity_id=eid,
            role=role_norm,
            notes=item.get("notes"),
        )
        db.add(link)
        out.append(link)
    return out


def create_document(db: Session, payload: Dict[str, Any]) -> Document:
    _ensure_document_anchor(payload)
    is_ref = bool(payload.get("is_reference_only", False))
    storage_path = _validate_storage_path(payload.get("storage_path"), is_ref)
    doc = Document(
        title=(str(payload["title"]).strip() if payload.get("title") else None),
        document_type=(
            str(payload["document_type"]).strip() if payload.get("document_type") else None
        ),
        description=payload.get("description"),
        origin_type=(str(payload.get("origin_type") or "manual")),
        source_locator=payload.get("source_locator"),
        mime_type=payload.get("mime_type"),
        storage_path=storage_path,
        checksum=payload.get("checksum"),
        content_hash=payload.get("content_hash"),
        size_bytes=payload.get("size_bytes"),
        language=payload.get("language"),
        published_at=payload.get("published_at"),
        occurred_at=payload.get("occurred_at"),
        captured_at=payload.get("captured_at"),
        collected_at=payload.get("collected_at") or _utcnow(),
        verification_status=(
            str(payload.get("verification_status") or "nao_verificado")
            if str(payload.get("verification_status") or "nao_verificado") in VERIFICATION_STATUSES
            else "nao_verificado"
        ),
        access_level=payload.get("access_level"),
        license_terms=payload.get("license_terms"),
        is_reference_only=is_ref,
        metadata_json=payload.get("metadata_json"),
        source_id=payload.get("source_id"),
        raw_record_id=payload.get("raw_record_id"),
        research_source_id=payload.get("research_source_id"),
    )
    if not doc.is_reference_only and doc.storage_path and not doc.content_hash:
        h, sz = _compute_hash_for_path(doc.storage_path)
        if h:
            doc.content_hash = h
            if doc.size_bytes is None and sz is not None:
                doc.size_bytes = sz
            if not doc.checksum:
                doc.checksum = h
    db.add(doc)
    db.flush()

    entity_ids = payload.get("entity_ids") or []
    link_items = [{"entity_id": eid, "role": payload.get("entity_role")} for eid in entity_ids]
    links = sync_document_entity_links(db, doc, link_items)
    db.flush()

    record_processing_event(
        db,
        stage="dossier_document_register",
        status="completed",
        message="Document registered (deterministic/manual)",
        payload={
            "document_id": doc.id,
            "entity_count": len(links),
            "has_hash": bool(doc.content_hash),
        },
    )
    snap = _document_snapshot(doc, links)
    record_data_change(
        db,
        entity_table="documents",
        entity_id=doc.id,
        change_type="create",
        before=None,
        after=_jsonable(snap),
        reason="dossier.document.create",
    )
    record_audit(
        db,
        action="dossier.document.create",
        target_type="document",
        target_id=doc.id,
        details={"title": doc.title, "document_type": doc.document_type},
    )
    return doc


def get_document(db: Session, document_id: str) -> Optional[Document]:
    return db.get(Document, document_id)


@dataclass
class ListDocumentsResult:
    items: List[Document]
    total: int


def list_documents_for_entity(
    db: Session,
    entity_id: str,
    *,
    q: Optional[str] = None,
    document_type: Optional[str] = None,
    verification_status: Optional[str] = None,
    origin_type: Optional[str] = None,
    sort: str = "updated_desc",
    limit: int = 20,
    offset: int = 0,
) -> ListDocumentsResult:
    link_sub = select(DocumentEntityLink.document_id).where(
        DocumentEntityLink.entity_id == entity_id
    )
    stmt = select(Document).where(Document.id.in_(link_sub))
    count_stmt = select(func.count()).select_from(Document).where(Document.id.in_(link_sub))
    conds = []
    if document_type:
        conds.append(Document.document_type == document_type)
    if verification_status:
        conds.append(Document.verification_status == verification_status)
    if origin_type:
        conds.append(Document.origin_type == origin_type)
    if q:
        like = f"%{q.strip()}%"
        conds.append(
            or_(
                Document.title.like(like),
                Document.description.like(like),
                Document.source_locator.like(like),
            )
        )
    if conds:
        stmt = stmt.where(*conds)
        count_stmt = count_stmt.where(*conds)
    sort_map = {
        "updated_desc": Document.updated_at.desc(),
        "created_desc": Document.created_at.desc(),
        "published_desc": Document.published_at.desc(),
        "title_asc": Document.title.asc(),
    }
    stmt = stmt.order_by(sort_map.get(sort, Document.updated_at.desc()), Document.id.asc())
    stmt = stmt.limit(limit).offset(offset)
    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.execute(stmt).scalars().all())
    return ListDocumentsResult(items=items, total=total)


def update_document(db: Session, doc: Document, payload: Dict[str, Any]) -> Document:
    before_links = load_document_links(db, doc.id)
    before = _jsonable(_document_snapshot(doc, before_links))
    for field in [
        "title",
        "document_type",
        "description",
        "origin_type",
        "source_locator",
        "mime_type",
        "checksum",
        "content_hash",
        "size_bytes",
        "language",
        "published_at",
        "occurred_at",
        "captured_at",
        "access_level",
        "license_terms",
        "metadata_json",
        "source_id",
        "raw_record_id",
        "research_source_id",
    ]:
        if field in payload:
            setattr(doc, field, payload[field])
    if "is_reference_only" in payload and payload["is_reference_only"] is not None:
        doc.is_reference_only = bool(payload["is_reference_only"])
    if "storage_path" in payload:
        doc.storage_path = _validate_storage_path(
            payload.get("storage_path"), doc.is_reference_only
        )
    if "verification_status" in payload and payload["verification_status"] is not None:
        v = str(payload["verification_status"])
        doc.verification_status = v if v in VERIFICATION_STATUSES else doc.verification_status
    # ensure anchor still holds (best-effort)
    if not (doc.source_id or doc.raw_record_id or doc.research_source_id or doc.source_locator):
        raise ValueError("document must have at least one provenance anchor")
    db.flush()
    after_links = load_document_links(db, doc.id)
    after = _jsonable(_document_snapshot(doc, after_links))
    record_data_change(
        db,
        entity_table="documents",
        entity_id=doc.id,
        change_type="update",
        before=before,
        after=after,
        reason="dossier.document.update",
    )
    record_audit(
        db,
        action="dossier.document.update",
        target_type="document",
        target_id=doc.id,
        details={"title": doc.title},
    )
    return doc


def link_document_entities(
    db: Session, doc: Document, links: Iterable[Dict[str, Any]], replace: bool = False
) -> List[DocumentEntityLink]:
    before_links = load_document_links(db, doc.id)
    before = _jsonable(_document_snapshot(doc, before_links))
    if replace:
        new_links = sync_document_entity_links(db, doc, links)
    else:
        existing = {(link.entity_id, link.role or "") for link in before_links}
        new_links = list(before_links)
        for item in links:
            eid = str(item.get("entity_id") or "").strip()
            if not eid:
                continue
            role = item.get("role")
            role_norm = str(role).strip() if role is not None and str(role).strip() else None
            key = (eid, role_norm or "")
            if key in existing:
                continue
            if db.get(Entity, eid) is None:
                raise ValueError(f"linked entity not found: {eid}")
            link = DocumentEntityLink(
                document_id=doc.id,
                entity_id=eid,
                role=role_norm,
                notes=item.get("notes"),
            )
            db.add(link)
            new_links.append(link)
            existing.add(key)
    db.flush()
    after = _jsonable(_document_snapshot(doc, new_links))
    record_data_change(
        db,
        entity_table="documents",
        entity_id=doc.id,
        change_type="update",
        before=before,
        after=after,
        reason="dossier.document.link_entities",
    )
    record_audit(
        db,
        action="dossier.document.link_entities",
        target_type="document",
        target_id=doc.id,
        details={"count": len(new_links)},
    )
    return new_links


# ---------------- Claims ----------------


def load_claim_entity_links(db: Session, claim_id: str) -> List[ClaimEntityLink]:
    return list(
        db.execute(select(ClaimEntityLink).where(ClaimEntityLink.claim_id == claim_id))
        .scalars()
        .all()
    )


def load_claim_evidence(db: Session, claim_id: str) -> List[Evidence]:
    return list(db.execute(select(Evidence).where(Evidence.claim_id == claim_id)).scalars().all())


def load_claim_conflicts(db: Session, claim_id: str) -> List[ClaimConflict]:
    return list(
        db.execute(
            select(ClaimConflict).where(
                or_(
                    ClaimConflict.claim_id == claim_id,
                    ClaimConflict.conflicting_claim_id == claim_id,
                )
            )
        )
        .scalars()
        .all()
    )


def _claim_snapshot(claim: ExtractedClaim, links: Sequence[ClaimEntityLink]) -> Dict[str, Any]:
    return {
        "id": claim.id,
        "claim_text": claim.claim_text,
        "claim_type": claim.claim_type,
        "claim_origin": claim.claim_origin,
        "verification_status": claim.verification_status,
        "conflict_status": claim.conflict_status,
        "confidence": claim.confidence,
        "justification": claim.justification,
        "entity_id": claim.entity_id,
        "source_id": claim.source_id,
        "raw_record_id": claim.raw_record_id,
        "document_id": claim.document_id,
        "research_source_id": claim.research_source_id,
        "registered_at": claim.registered_at.isoformat() if claim.registered_at else None,
        "published_at": claim.published_at.isoformat() if claim.published_at else None,
        "occurred_at": claim.occurred_at.isoformat() if claim.occurred_at else None,
        "entity_links": [
            {"entity_id": link.entity_id, "relevance": link.relevance} for link in links
        ],
    }


def sync_claim_entity_links(
    db: Session,
    claim: ExtractedClaim,
    entity_ids: Iterable[str],
    primary_entity_id: Optional[str] = None,
) -> List[ClaimEntityLink]:
    ids = [str(e).strip() for e in entity_ids if str(e).strip()]
    if primary_entity_id:
        primary = str(primary_entity_id).strip()
        ids = [primary] + [i for i in ids if i != primary]
    # unique preserve order
    seen = set()
    uniq: List[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    db.query(ClaimEntityLink).filter(ClaimEntityLink.claim_id == claim.id).delete(
        synchronize_session=False
    )
    out: List[ClaimEntityLink] = []
    for eid in uniq:
        if db.get(Entity, eid) is None:
            raise ValueError(f"linked entity not found: {eid}")
        link = ClaimEntityLink(claim_id=claim.id, entity_id=eid)
        db.add(link)
        out.append(link)
    if uniq:
        claim.entity_id = uniq[0]
    return out


def create_claim(db: Session, entity_id: str, payload: Dict[str, Any]) -> ExtractedClaim:
    ensure_entity(db, entity_id)
    text = str(payload.get("claim_text") or "").strip()
    if not text:
        raise ValueError("claim_text is required")
    claim_type = str(payload.get("claim_type") or ClaimType.DECLARACAO.value)
    if claim_type not in CLAIM_TYPES:
        claim_type = ClaimType.DECLARACAO.value
    vstatus = str(payload.get("verification_status") or VerificationStatus.NAO_VERIFICADO.value)
    if vstatus not in VERIFICATION_STATUSES:
        vstatus = VerificationStatus.NAO_VERIFICADO.value
    origin = str(payload.get("claim_origin") or "manual")
    if origin not in CLAIM_ORIGINS:
        origin = "manual"
    # epistemic guard: no automatic promotion of inference/hypothesis/prediction to verified fact
    if (
        claim_type in {"inferencia", "hipotese", "previsao"}
        and vstatus == VerificationStatus.VERIFICADO.value
    ):
        # require explicit justification, but still allow explicit manual marking
        if not str(payload.get("justification") or "").strip():
            raise ValueError("justification is required for explicitly verified inferential claims")
    claim = ExtractedClaim(
        claim_text=text,
        claim_type=claim_type,
        claim_origin=origin,
        verification_status=vstatus,
        confidence=payload.get("confidence"),
        justification=payload.get("justification"),
        source_id=payload.get("source_id"),
        raw_record_id=payload.get("raw_record_id"),
        document_id=payload.get("document_id"),
        research_source_id=payload.get("research_source_id"),
        entity_id=entity_id,
        registered_at=payload.get("registered_at") or _utcnow(),
        published_at=payload.get("published_at"),
        collected_at=payload.get("collected_at"),
        occurred_at=payload.get("occurred_at"),
        valid_from=payload.get("valid_from"),
        valid_to=payload.get("valid_to"),
        structured_json=payload.get("structured_json"),
        metadata_json=payload.get("metadata_json"),
        conflict_status="none",
    )
    db.add(claim)
    db.flush()
    links = sync_claim_entity_links(
        db, claim, payload.get("entity_ids") or [], primary_entity_id=entity_id
    )
    db.flush()
    snap = _claim_snapshot(claim, links)
    record_data_change(
        db,
        entity_table="extracted_claims",
        entity_id=claim.id,
        change_type="create",
        before=None,
        after=_jsonable(snap),
        reason="dossier.claim.create",
    )
    record_audit(
        db,
        action="dossier.claim.create",
        target_type="claim",
        target_id=claim.id,
        details={"entity_id": entity_id, "claim_type": claim.claim_type},
    )
    return claim


def get_claim(db: Session, claim_id: str) -> Optional[ExtractedClaim]:
    return db.get(ExtractedClaim, claim_id)


@dataclass
class ListClaimsResult:
    items: List[ExtractedClaim]
    total: int


def list_claims_for_entity(
    db: Session,
    entity_id: str,
    *,
    q: Optional[str] = None,
    claim_type: Optional[str] = None,
    verification_status: Optional[str] = None,
    conflict_status: Optional[str] = None,
    sort: str = "updated_desc",
    limit: int = 20,
    offset: int = 0,
) -> ListClaimsResult:
    link_sub = select(ClaimEntityLink.claim_id).where(ClaimEntityLink.entity_id == entity_id)
    stmt = select(ExtractedClaim).where(
        or_(ExtractedClaim.id.in_(link_sub), ExtractedClaim.entity_id == entity_id)
    )
    count_stmt = (
        select(func.count())
        .select_from(ExtractedClaim)
        .where(or_(ExtractedClaim.id.in_(link_sub), ExtractedClaim.entity_id == entity_id))
    )
    conds = []
    if claim_type:
        conds.append(ExtractedClaim.claim_type == claim_type)
    if verification_status:
        conds.append(ExtractedClaim.verification_status == verification_status)
    if conflict_status:
        conds.append(ExtractedClaim.conflict_status == conflict_status)
    if q:
        conds.append(ExtractedClaim.claim_text.like(f"%{q.strip()}%"))
    if conds:
        stmt = stmt.where(*conds)
        count_stmt = count_stmt.where(*conds)
    sort_map = {
        "updated_desc": ExtractedClaim.updated_at.desc(),
        "created_desc": ExtractedClaim.created_at.desc(),
        "occurred_desc": ExtractedClaim.occurred_at.desc(),
    }
    stmt = stmt.order_by(
        sort_map.get(sort, ExtractedClaim.updated_at.desc()), ExtractedClaim.id.asc()
    )
    stmt = stmt.limit(limit).offset(offset)
    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.execute(stmt).scalars().all())
    return ListClaimsResult(items=items, total=total)


def update_claim(db: Session, claim: ExtractedClaim, payload: Dict[str, Any]) -> ExtractedClaim:
    before_links = load_claim_entity_links(db, claim.id)
    before = _jsonable(_claim_snapshot(claim, before_links))
    if "claim_text" in payload and payload["claim_text"] is not None:
        txt = str(payload["claim_text"]).strip()
        if not txt:
            raise ValueError("claim_text cannot be empty")
        claim.claim_text = txt
    for field in [
        "confidence",
        "justification",
        "source_id",
        "raw_record_id",
        "document_id",
        "research_source_id",
        "published_at",
        "occurred_at",
        "valid_from",
        "valid_to",
        "structured_json",
        "metadata_json",
    ]:
        if field in payload:
            setattr(claim, field, payload[field])
    if "claim_type" in payload and payload["claim_type"] is not None:
        v = str(payload["claim_type"])
        claim.claim_type = v if v in CLAIM_TYPES else claim.claim_type
    if "verification_status" in payload and payload["verification_status"] is not None:
        v = str(payload["verification_status"])
        if v in VERIFICATION_STATUSES:
            claim.verification_status = v
    if "conflict_status" in payload and payload["conflict_status"] is not None:
        v = str(payload["conflict_status"])
        if v in CLAIM_CONFLICT_STATES:
            claim.conflict_status = v
    if "entity_ids" in payload and payload["entity_ids"] is not None:
        sync_claim_entity_links(
            db, claim, payload["entity_ids"] or [], primary_entity_id=claim.entity_id
        )
    db.flush()
    after_links = load_claim_entity_links(db, claim.id)
    after = _jsonable(_claim_snapshot(claim, after_links))
    record_data_change(
        db,
        entity_table="extracted_claims",
        entity_id=claim.id,
        change_type="update",
        before=before,
        after=after,
        reason="dossier.claim.update",
    )
    record_audit(
        db,
        action="dossier.claim.update",
        target_type="claim",
        target_id=claim.id,
        details={"claim_type": claim.claim_type},
    )
    return claim


# ---------------- Evidence ----------------


def _evidence_snapshot(ev: Evidence) -> Dict[str, Any]:
    return {
        "id": ev.id,
        "claim_id": ev.claim_id,
        "evidence_type": ev.evidence_type,
        "relation_type": ev.relation_type,
        "document_id": ev.document_id,
        "research_source_id": ev.research_source_id,
        "source_id": ev.source_id,
        "raw_record_id": ev.raw_record_id,
        "locator": ev.locator,
        "location_json": ev.location_json,
        "snippet": ev.snippet,
        "excerpt": ev.excerpt,
        "note": ev.note,
        "verification_status": ev.verification_status,
        "confidence": ev.confidence,
    }


def _ensure_evidence_anchor(payload: Dict[str, Any]) -> None:
    if any(
        payload.get(k)
        for k in [
            "document_id",
            "research_source_id",
            "raw_record_id",
            "source_id",
            "locator",
            "snippet",
            "excerpt",
        ]
    ):
        return
    raise ValueError(
        "evidence must reference at least one anchor "
        "(document, research source, raw record, source, locator, or excerpt)"
    )


def create_evidence(db: Session, claim_id: str, payload: Dict[str, Any]) -> Evidence:
    claim = db.get(ExtractedClaim, claim_id)
    if claim is None:
        raise ValueError("claim not found")
    _ensure_evidence_anchor(payload)
    rel = str(payload.get("relation_type") or "supports")
    if rel not in EVIDENCE_RELATION_TYPES:
        raise ValueError("invalid relation_type")
    vstatus = str(payload.get("verification_status") or VerificationStatus.NAO_VERIFICADO.value)
    if vstatus not in VERIFICATION_STATUSES:
        vstatus = VerificationStatus.NAO_VERIFICADO.value
    ev = Evidence(
        claim_id=claim_id,
        evidence_type=payload.get("evidence_type"),
        relation_type=rel,
        document_id=payload.get("document_id"),
        research_source_id=payload.get("research_source_id"),
        source_id=payload.get("source_id"),
        raw_record_id=payload.get("raw_record_id"),
        locator=payload.get("locator"),
        location_json=payload.get("location_json"),
        snippet=payload.get("snippet"),
        excerpt=payload.get("excerpt"),
        note=payload.get("note"),
        published_at=payload.get("published_at"),
        collected_at=payload.get("collected_at"),
        confidence=payload.get("confidence"),
        verification_status=vstatus,
    )
    db.add(ev)
    db.flush()
    record_data_change(
        db,
        entity_table="evidence",
        entity_id=ev.id,
        change_type="create",
        before=None,
        after=_jsonable(_evidence_snapshot(ev)),
        reason="dossier.evidence.create",
    )
    record_audit(
        db,
        action="dossier.evidence.create",
        target_type="evidence",
        target_id=ev.id,
        details={"claim_id": claim_id, "relation_type": ev.relation_type},
    )
    return ev


def get_evidence(db: Session, evidence_id: str) -> Optional[Evidence]:
    return db.get(Evidence, evidence_id)


@dataclass
class ListEvidenceResult:
    items: List[Evidence]
    total: int


def list_evidence_for_claim(db: Session, claim_id: str) -> ListEvidenceResult:
    items = load_claim_evidence(db, claim_id)
    return ListEvidenceResult(items=items, total=len(items))


def update_evidence(db: Session, ev: Evidence, payload: Dict[str, Any]) -> Evidence:
    before = _jsonable(_evidence_snapshot(ev))
    for field in [
        "evidence_type",
        "document_id",
        "research_source_id",
        "source_id",
        "raw_record_id",
        "locator",
        "location_json",
        "snippet",
        "excerpt",
        "note",
        "published_at",
        "collected_at",
        "confidence",
    ]:
        if field in payload:
            setattr(ev, field, payload[field])
    if "relation_type" in payload and payload["relation_type"] is not None:
        rel = str(payload["relation_type"])
        if rel in EVIDENCE_RELATION_TYPES:
            ev.relation_type = rel
    if "verification_status" in payload and payload["verification_status"] is not None:
        v = str(payload["verification_status"])
        if v in VERIFICATION_STATUSES:
            ev.verification_status = v
    # validate anchor still present
    if not any(
        [
            ev.document_id,
            ev.research_source_id,
            ev.raw_record_id,
            ev.source_id,
            ev.locator,
            ev.snippet,
            ev.excerpt,
        ]
    ):
        raise ValueError("evidence must reference at least one anchor")
    db.flush()
    record_data_change(
        db,
        entity_table="evidence",
        entity_id=ev.id,
        change_type="update",
        before=before,
        after=_jsonable(_evidence_snapshot(ev)),
        reason="dossier.evidence.update",
    )
    record_audit(
        db,
        action="dossier.evidence.update",
        target_type="evidence",
        target_id=ev.id,
        details={"claim_id": ev.claim_id},
    )
    return ev


# ---------------- Conflicts ----------------


def _conflict_snapshot(c: ClaimConflict) -> Dict[str, Any]:
    return {
        "id": c.id,
        "claim_id": c.claim_id,
        "conflicting_claim_id": c.conflicting_claim_id,
        "conflict_type": c.conflict_type,
        "description": c.description,
        "status": c.status,
        "detected_by": c.detected_by,
        "created_by": c.created_by,
    }


def _recompute_claim_conflict_state(db: Session, claim_id: str) -> None:
    claim = db.get(ExtractedClaim, claim_id)
    if claim is None:
        return
    conflicts = load_claim_conflicts(db, claim_id)
    active = [c for c in conflicts if c.status in {"open", "under_review"}]
    if any(c.status == "open" for c in active):
        claim.conflict_status = "conflicting"
    elif any(c.status == "under_review" for c in active):
        claim.conflict_status = "under_review"
    else:
        claim.conflict_status = "none"


def create_claim_conflict(db: Session, claim_id: str, payload: Dict[str, Any]) -> ClaimConflict:
    claim = db.get(ExtractedClaim, claim_id)
    if claim is None:
        raise ValueError("claim not found")
    other_id = str(payload.get("conflicting_claim_id") or "").strip()
    if not other_id:
        raise ValueError("conflicting_claim_id is required")
    if other_id == claim_id:
        raise ValueError("claim cannot conflict with itself")
    other = db.get(ExtractedClaim, other_id)
    if other is None:
        raise ValueError("conflicting claim not found")
    ctype = str(payload.get("conflict_type") or "").strip()
    if not ctype:
        raise ValueError("conflict_type is required")
    status = str(payload.get("status") or "open")
    if status not in CONFLICT_STATUSES:
        status = "open"
    a, b = sorted([claim_id, other_id])
    existing = db.execute(
        select(ClaimConflict).where(
            ClaimConflict.claim_id == a, ClaimConflict.conflicting_claim_id == b
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("conflict already exists for this claim pair")
    conflict = ClaimConflict(
        claim_id=a,
        conflicting_claim_id=b,
        conflict_type=ctype,
        description=payload.get("description"),
        status=status,
        detected_by="user",
        created_by=payload.get("created_by") or "local",
    )
    db.add(conflict)
    db.flush()
    _recompute_claim_conflict_state(db, claim_id)
    _recompute_claim_conflict_state(db, other_id)
    db.flush()
    record_data_change(
        db,
        entity_table="claim_conflicts",
        entity_id=conflict.id,
        change_type="create",
        before=None,
        after=_jsonable(_conflict_snapshot(conflict)),
        reason="dossier.claim_conflict.create",
    )
    record_audit(
        db,
        action="dossier.claim_conflict.create",
        target_type="claim_conflict",
        target_id=conflict.id,
        details={"claim_id": claim_id, "conflicting_claim_id": other_id},
    )
    return conflict


def get_claim_conflict(db: Session, conflict_id: str) -> Optional[ClaimConflict]:
    return db.get(ClaimConflict, conflict_id)


def update_claim_conflict(
    db: Session, conflict: ClaimConflict, payload: Dict[str, Any]
) -> ClaimConflict:
    before = _jsonable(_conflict_snapshot(conflict))
    if "conflict_type" in payload and payload["conflict_type"] is not None:
        ctype = str(payload["conflict_type"]).strip()
        if ctype:
            conflict.conflict_type = ctype
    if "description" in payload:
        conflict.description = payload["description"]
    if "status" in payload and payload["status"] is not None:
        st = str(payload["status"])
        if st in CONFLICT_STATUSES:
            conflict.status = st
    db.flush()
    _recompute_claim_conflict_state(db, conflict.claim_id)
    _recompute_claim_conflict_state(db, conflict.conflicting_claim_id)
    db.flush()
    record_data_change(
        db,
        entity_table="claim_conflicts",
        entity_id=conflict.id,
        change_type="update",
        before=before,
        after=_jsonable(_conflict_snapshot(conflict)),
        reason="dossier.claim_conflict.update",
    )
    record_audit(
        db,
        action="dossier.claim_conflict.update",
        target_type="claim_conflict",
        target_id=conflict.id,
        details={"status": conflict.status},
    )
    return conflict


@dataclass
class ListConflictsResult:
    items: List[ClaimConflict]
    total: int


def list_conflicts_for_entity(
    db: Session, entity_id: str, *, status: Optional[str] = None, limit: int = 50, offset: int = 0
) -> ListConflictsResult:
    link_sub = select(ClaimEntityLink.claim_id).where(ClaimEntityLink.entity_id == entity_id)
    entity_claim_ids = select(ExtractedClaim.id).where(ExtractedClaim.entity_id == entity_id)
    cond_claim = or_(
        ClaimConflict.claim_id.in_(link_sub),
        ClaimConflict.conflicting_claim_id.in_(link_sub),
        ClaimConflict.claim_id.in_(entity_claim_ids),
        ClaimConflict.conflicting_claim_id.in_(entity_claim_ids),
    )
    stmt = select(ClaimConflict).where(cond_claim)
    count_stmt = select(func.count()).select_from(ClaimConflict).where(cond_claim)
    if status:
        stmt = stmt.where(ClaimConflict.status == status)
        count_stmt = count_stmt.where(ClaimConflict.status == status)
    stmt = stmt.order_by(ClaimConflict.updated_at.desc()).limit(limit).offset(offset)
    total = int(db.execute(count_stmt).scalar_one() or 0)
    items = list(db.execute(stmt).scalars().all())
    return ListConflictsResult(items=items, total=total)


# ---------------- Research summary ----------------


def research_summary(db: Session, entity_id: str) -> Dict[str, Any]:
    ensure_entity(db, entity_id)
    doc_sub = select(DocumentEntityLink.document_id).where(
        DocumentEntityLink.entity_id == entity_id
    )
    documents_count = int(
        db.execute(
            select(func.count()).select_from(Document).where(Document.id.in_(doc_sub))
        ).scalar_one()
        or 0
    )
    # research sources referenced by docs or claims linked to entity
    claim_sub = select(ClaimEntityLink.claim_id).where(ClaimEntityLink.entity_id == entity_id)
    claim_cond = or_(ExtractedClaim.id.in_(claim_sub), ExtractedClaim.entity_id == entity_id)
    claim_ids_stmt = select(ExtractedClaim.id).where(claim_cond)
    claims_count = int(
        db.execute(select(func.count()).select_from(ExtractedClaim).where(claim_cond)).scalar_one()
        or 0
    )
    rs_from_docs = select(Document.research_source_id).where(
        Document.id.in_(doc_sub), Document.research_source_id.is_not(None)
    )
    rs_from_claims = select(ExtractedClaim.research_source_id).where(
        claim_cond, ExtractedClaim.research_source_id.is_not(None)
    )
    rs_from_ev = select(Evidence.research_source_id).where(
        Evidence.claim_id.in_(claim_ids_stmt),
        Evidence.research_source_id.is_not(None),
    )
    # union count distinct
    rs_ids = set()
    for row in db.execute(rs_from_docs).all():
        if row[0]:
            rs_ids.add(row[0])
    for row in db.execute(rs_from_claims).all():
        if row[0]:
            rs_ids.add(row[0])
    for row in db.execute(rs_from_ev).all():
        if row[0]:
            rs_ids.add(row[0])
    evidence_count = int(
        db.execute(
            select(func.count()).select_from(Evidence).where(Evidence.claim_id.in_(claim_ids_stmt))
        ).scalar_one()
        or 0
    )
    pending_verification_claims = int(
        db.execute(
            select(func.count())
            .select_from(ExtractedClaim)
            .where(
                claim_cond,
                ExtractedClaim.verification_status.in_(["nao_verificado", "em_verificacao"]),
            )
        ).scalar_one()
        or 0
    )
    open_conflicts = int(
        db.execute(
            select(func.count())
            .select_from(ClaimConflict)
            .where(
                or_(
                    ClaimConflict.claim_id.in_(claim_ids_stmt),
                    ClaimConflict.conflicting_claim_id.in_(claim_ids_stmt),
                ),
                ClaimConflict.status.in_(["open", "under_review"]),
            )
        ).scalar_one()
        or 0
    )
    claims_by_type: Dict[str, int] = {}
    for t, c in db.execute(
        select(ExtractedClaim.claim_type, func.count())
        .where(claim_cond)
        .group_by(ExtractedClaim.claim_type)
    ).all():
        claims_by_type[str(t)] = int(c)
    claims_by_verification: Dict[str, int] = {}
    for t, c in db.execute(
        select(ExtractedClaim.verification_status, func.count())
        .where(claim_cond)
        .group_by(ExtractedClaim.verification_status)
    ).all():
        claims_by_verification[str(t)] = int(c)
    return {
        "entity_id": entity_id,
        "documents_count": documents_count,
        "research_sources_count": len(rs_ids),
        "claims_count": claims_count,
        "evidence_count": evidence_count,
        "pending_verification_claims": pending_verification_claims,
        "open_conflicts": open_conflicts,
        "claims_by_type": claims_by_type,
        "claims_by_verification": claims_by_verification,
    }
