from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.dossiers_research import (
    ClaimConflictCreate,
    ClaimConflictDetail,
    ClaimConflictListResponse,
    ClaimConflictSummary,
    ClaimConflictUpdate,
    ClaimCreate,
    ClaimDetail,
    ClaimEntityLinkResponse,
    ClaimListResponse,
    ClaimSummary,
    ClaimUpdate,
    DocumentCreate,
    DocumentDetail,
    DocumentEntityLinkInput,
    DocumentEntityLinkResponse,
    DocumentListResponse,
    DocumentSummary,
    DocumentUpdate,
    EvidenceCreate,
    EvidenceDetail,
    EvidenceListResponse,
    EvidenceSummary,
    EvidenceUpdate,
    ResearchSourceCreate,
    ResearchSourceDetail,
    ResearchSourceListResponse,
    ResearchSourceSummary,
    ResearchSourceUpdate,
    ResearchSummaryResponse,
)
from app.db.session import get_db
from app.knowledge.dossiers.research_service import (
    create_claim,
    create_claim_conflict,
    create_document,
    create_evidence,
    create_research_source,
    get_claim,
    get_claim_conflict,
    get_document,
    get_evidence,
    get_research_source,
    link_document_entities,
    list_claims_for_entity,
    list_conflicts_for_entity,
    list_documents_for_entity,
    list_evidence_for_claim,
    list_research_sources,
    load_claim_conflicts,
    load_claim_entity_links,
    load_claim_evidence,
    load_document_links,
    research_summary,
    update_claim,
    update_claim_conflict,
    update_document,
    update_evidence,
    update_research_source,
)
from app.knowledge.dossiers.service import get_entity
from app.knowledge.models.domain import Document, ExtractedClaim

router = APIRouter(prefix="/dossiers", tags=["dossiers"])


def _ensure_entity_exists(db: Session, entity_id: str) -> None:
    if get_entity(db, entity_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found")


# --- Research Sources ---


@router.post(
    "/research-sources",
    response_model=ResearchSourceDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_research_source_endpoint(
    payload: ResearchSourceCreate, db: Session = Depends(get_db)
) -> ResearchSourceDetail:
    try:
        rs = create_research_source(db, payload.model_dump())
        db.commit()
        db.refresh(rs)
        return ResearchSourceDetail.model_validate(rs)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/research-sources", response_model=ResearchSourceListResponse)
def list_research_sources_endpoint(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(default=None),
    source_type: Optional[str] = Query(default=None),
    classification: Optional[str] = Query(default=None),
    reliability_status: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    sort: str = Query(default="updated_desc"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ResearchSourceListResponse:
    result = list_research_sources(
        db,
        q=q,
        source_type=source_type,
        classification=classification,
        reliability_status=reliability_status,
        verification_status=verification_status,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ResearchSourceListResponse(
        items=[ResearchSourceSummary.model_validate(x) for x in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/research-sources/{source_id}", response_model=ResearchSourceDetail)
def get_research_source_endpoint(
    source_id: str, db: Session = Depends(get_db)
) -> ResearchSourceDetail:
    rs = get_research_source(db, source_id)
    if rs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Research source not found"
        )
    return ResearchSourceDetail.model_validate(rs)


@router.patch("/research-sources/{source_id}", response_model=ResearchSourceDetail)
def update_research_source_endpoint(
    source_id: str, payload: ResearchSourceUpdate, db: Session = Depends(get_db)
) -> ResearchSourceDetail:
    rs = get_research_source(db, source_id)
    if rs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Research source not found"
        )
    try:
        rs = update_research_source(db, rs, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(rs)
        return ResearchSourceDetail.model_validate(rs)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


# --- Documents ---


def _document_detail(db: Session, doc: Document) -> DocumentDetail:
    links = load_document_links(db, doc.id)
    base = DocumentDetail.model_validate(doc)
    base.entity_links = [DocumentEntityLinkResponse.model_validate(link) for link in links]
    return base


@router.post(
    "/entities/{entity_id}/documents",
    response_model=DocumentDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_document_endpoint(
    entity_id: str, payload: DocumentCreate, db: Session = Depends(get_db)
) -> DocumentDetail:
    _ensure_entity_exists(db, entity_id)
    try:
        data = payload.model_dump()
        # ensure primary entity is associated
        eids = list(data.get("entity_ids") or [])
        if entity_id not in eids:
            eids = [entity_id] + eids
        data["entity_ids"] = eids
        doc = create_document(db, data)
        db.commit()
        db.refresh(doc)
        return _document_detail(db, doc)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc


@router.get("/entities/{entity_id}/documents", response_model=DocumentListResponse)
def list_entity_documents_endpoint(
    entity_id: str,
    db: Session = Depends(get_db),
    q: Optional[str] = Query(default=None),
    document_type: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    origin_type: Optional[str] = Query(default=None),
    sort: str = Query(default="updated_desc"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> DocumentListResponse:
    _ensure_entity_exists(db, entity_id)
    result = list_documents_for_entity(
        db,
        entity_id,
        q=q,
        document_type=document_type,
        verification_status=verification_status,
        origin_type=origin_type,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return DocumentListResponse(
        items=[DocumentSummary.model_validate(x) for x in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document_endpoint(document_id: str, db: Session = Depends(get_db)) -> DocumentDetail:
    doc = get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _document_detail(db, doc)


@router.patch("/documents/{document_id}", response_model=DocumentDetail)
def update_document_endpoint(
    document_id: str, payload: DocumentUpdate, db: Session = Depends(get_db)
) -> DocumentDetail:
    doc = get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    try:
        doc = update_document(db, doc, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(doc)
        return _document_detail(db, doc)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post(
    "/documents/{document_id}/entities",
    response_model=list[DocumentEntityLinkResponse],
)
def link_document_entities_endpoint(
    document_id: str, payload: list[DocumentEntityLinkInput], db: Session = Depends(get_db)
) -> list[DocumentEntityLinkResponse]:
    doc = get_document(db, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    try:
        links = link_document_entities(db, doc, [p.model_dump() for p in payload], replace=False)
        db.commit()
        return [DocumentEntityLinkResponse.model_validate(link) for link in links]
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc


# --- Claims ---


def _claim_detail(db: Session, claim: ExtractedClaim) -> ClaimDetail:
    links = load_claim_entity_links(db, claim.id)
    evidence = load_claim_evidence(db, claim.id)
    conflicts = load_claim_conflicts(db, claim.id)
    detail = ClaimDetail.model_validate(claim)
    detail.entity_links = [ClaimEntityLinkResponse.model_validate(link) for link in links]
    detail.evidence = [EvidenceSummary.model_validate(e) for e in evidence]
    detail.conflicts = [ClaimConflictSummary.model_validate(c) for c in conflicts]
    return detail


@router.post(
    "/entities/{entity_id}/claims",
    response_model=ClaimDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_claim_endpoint(
    entity_id: str, payload: ClaimCreate, db: Session = Depends(get_db)
) -> ClaimDetail:
    _ensure_entity_exists(db, entity_id)
    try:
        claim = create_claim(db, entity_id, payload.model_dump())
        db.commit()
        db.refresh(claim)
        return _claim_detail(db, claim)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc


@router.get("/entities/{entity_id}/claims", response_model=ClaimListResponse)
def list_entity_claims_endpoint(
    entity_id: str,
    db: Session = Depends(get_db),
    q: Optional[str] = Query(default=None),
    claim_type: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    conflict_status: Optional[str] = Query(default=None),
    sort: str = Query(default="updated_desc"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ClaimListResponse:
    _ensure_entity_exists(db, entity_id)
    result = list_claims_for_entity(
        db,
        entity_id,
        q=q,
        claim_type=claim_type,
        verification_status=verification_status,
        conflict_status=conflict_status,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ClaimListResponse(
        items=[ClaimSummary.model_validate(x) for x in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get("/claims/{claim_id}", response_model=ClaimDetail)
def get_claim_endpoint(claim_id: str, db: Session = Depends(get_db)) -> ClaimDetail:
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    return _claim_detail(db, claim)


@router.patch("/claims/{claim_id}", response_model=ClaimDetail)
def update_claim_endpoint(
    claim_id: str, payload: ClaimUpdate, db: Session = Depends(get_db)
) -> ClaimDetail:
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    try:
        claim = update_claim(db, claim, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(claim)
        return _claim_detail(db, claim)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc


# --- Conflicts ---


@router.post(
    "/claims/{claim_id}/conflicts",
    response_model=ClaimConflictDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_claim_conflict_endpoint(
    claim_id: str, payload: ClaimConflictCreate, db: Session = Depends(get_db)
) -> ClaimConflictDetail:
    try:
        conflict = create_claim_conflict(db, claim_id, payload.model_dump())
        db.commit()
        db.refresh(conflict)
        return ClaimConflictDetail.model_validate(conflict)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        if "already exists" in msg.lower():
            code = status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=msg) from exc


@router.patch("/claims/{claim_id}/conflicts/{conflict_id}", response_model=ClaimConflictDetail)
def update_claim_conflict_endpoint(
    claim_id: str, conflict_id: str, payload: ClaimConflictUpdate, db: Session = Depends(get_db)
) -> ClaimConflictDetail:
    conflict = get_claim_conflict(db, conflict_id)
    if conflict is None or claim_id not in {conflict.claim_id, conflict.conflicting_claim_id}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict not found")
    try:
        conflict = update_claim_conflict(db, conflict, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(conflict)
        return ClaimConflictDetail.model_validate(conflict)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.get("/entities/{entity_id}/conflicts", response_model=ClaimConflictListResponse)
def list_entity_conflicts_endpoint(
    entity_id: str,
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ClaimConflictListResponse:
    _ensure_entity_exists(db, entity_id)
    result = list_conflicts_for_entity(
        db, entity_id, status=status_filter, limit=limit, offset=offset
    )
    return ClaimConflictListResponse(
        items=[ClaimConflictSummary.model_validate(x) for x in result.items],
        total=result.total,
        limit=limit,
        offset=offset,
    )


# --- Evidence ---


@router.post(
    "/claims/{claim_id}/evidence",
    response_model=EvidenceDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence_endpoint(
    claim_id: str, payload: EvidenceCreate, db: Session = Depends(get_db)
) -> EvidenceDetail:
    try:
        ev = create_evidence(db, claim_id, payload.model_dump())
        db.commit()
        db.refresh(ev)
        return EvidenceDetail.model_validate(ev)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc


@router.get("/claims/{claim_id}/evidence", response_model=EvidenceListResponse)
def list_claim_evidence_endpoint(
    claim_id: str, db: Session = Depends(get_db)
) -> EvidenceListResponse:
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    result = list_evidence_for_claim(db, claim_id)
    return EvidenceListResponse(
        items=[EvidenceSummary.model_validate(x) for x in result.items],
        total=result.total,
        limit=result.total,
        offset=0,
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceDetail)
def get_evidence_endpoint(evidence_id: str, db: Session = Depends(get_db)) -> EvidenceDetail:
    ev = get_evidence(db, evidence_id)
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return EvidenceDetail.model_validate(ev)


@router.patch("/evidence/{evidence_id}", response_model=EvidenceDetail)
def update_evidence_endpoint(
    evidence_id: str, payload: EvidenceUpdate, db: Session = Depends(get_db)
) -> EvidenceDetail:
    ev = get_evidence(db, evidence_id)
    if ev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    try:
        ev = update_evidence(db, ev, payload.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(ev)
        return EvidenceDetail.model_validate(ev)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


# --- Research Workspace Summary ---


@router.get("/entities/{entity_id}/research/summary", response_model=ResearchSummaryResponse)
def research_summary_endpoint(
    entity_id: str, db: Session = Depends(get_db)
) -> ResearchSummaryResponse:
    _ensure_entity_exists(db, entity_id)
    try:
        data = research_summary(db, entity_id)
        return ResearchSummaryResponse.model_validate(data)
    except ValueError as exc:
        db.rollback()
        msg = str(exc)
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        if "not found" in msg.lower():
            code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=msg) from exc
