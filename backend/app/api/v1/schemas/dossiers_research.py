from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# --- Research Sources ---

ReliabilityStatus = Literal["nao_avaliada", "baixa", "media", "alta", "contestada"]
ResearchVerificationStatus = Literal[
    "nao_verificado", "em_verificacao", "verificado", "contestado", "invalido"
]


class ResearchSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    source_type: str = Field(..., min_length=1, max_length=100)
    domain: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = Field(default=None, max_length=100)
    consulted_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    reliability_status: Optional[str] = Field(default="nao_avaliada", max_length=50)
    reliability_justification: Optional[str] = None
    verification_status: Optional[str] = Field(default="nao_verificado", max_length=50)
    ingestion_source_id: Optional[str] = Field(default=None, max_length=36)
    metadata_json: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = Field(default=None, max_length=100)


class ResearchSourceCreate(ResearchSourceBase):
    pass


class ResearchSourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=300)
    source_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    domain: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = Field(default=None, max_length=100)
    consulted_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    reliability_status: Optional[str] = Field(default=None, max_length=50)
    reliability_justification: Optional[str] = None
    verification_status: Optional[str] = Field(default=None, max_length=50)
    ingestion_source_id: Optional[str] = Field(default=None, max_length=36)
    metadata_json: Optional[Dict[str, Any]] = None


class ResearchSourceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source_type: str
    domain: Optional[str] = None
    url: Optional[str] = None
    classification: Optional[str] = None
    consulted_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    reliability_status: str
    verification_status: str
    ingestion_source_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResearchSourceDetail(ResearchSourceSummary):
    description: Optional[str] = None
    reliability_justification: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class ResearchSourceListResponse(BaseModel):
    items: List[ResearchSourceSummary]
    total: int
    limit: int
    offset: int


# --- Documents ---


class DocumentEntityLinkInput(BaseModel):
    entity_id: str = Field(..., min_length=1, max_length=36)
    role: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = None


class DocumentEntityLinkResponse(DocumentEntityLinkInput):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    created_at: datetime


class DocumentCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    document_type: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    origin_type: Optional[str] = Field(default="manual", max_length=50)
    source_locator: Optional[str] = None
    mime_type: Optional[str] = Field(default=None, max_length=200)
    storage_path: Optional[str] = None
    checksum: Optional[str] = Field(default=None, max_length=128)
    content_hash: Optional[str] = Field(default=None, max_length=128)
    size_bytes: Optional[int] = Field(default=None, ge=0)
    language: Optional[str] = Field(default=None, max_length=20)
    published_at: Optional[datetime] = None
    occurred_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    verification_status: Optional[str] = Field(default="nao_verificado", max_length=50)
    access_level: Optional[str] = Field(default=None, max_length=50)
    license_terms: Optional[str] = None
    is_reference_only: bool = False
    metadata_json: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = Field(default=None, max_length=36)  # ingestion source
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)
    entity_ids: List[str] = Field(default_factory=list)
    entity_role: Optional[str] = Field(default=None, max_length=100)


class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=500)
    document_type: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    origin_type: Optional[str] = Field(default=None, max_length=50)
    source_locator: Optional[str] = None
    mime_type: Optional[str] = Field(default=None, max_length=200)
    storage_path: Optional[str] = None
    checksum: Optional[str] = Field(default=None, max_length=128)
    content_hash: Optional[str] = Field(default=None, max_length=128)
    size_bytes: Optional[int] = Field(default=None, ge=0)
    language: Optional[str] = Field(default=None, max_length=20)
    published_at: Optional[datetime] = None
    occurred_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    verification_status: Optional[str] = Field(default=None, max_length=50)
    access_level: Optional[str] = Field(default=None, max_length=50)
    license_terms: Optional[str] = None
    is_reference_only: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = Field(default=None, max_length=36)
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str] = None
    document_type: Optional[str] = None
    origin_type: Optional[str] = None
    verification_status: str
    source_id: Optional[str] = None
    raw_record_id: Optional[str] = None
    research_source_id: Optional[str] = None
    source_locator: Optional[str] = None
    storage_path: Optional[str] = None
    is_reference_only: bool
    published_at: Optional[datetime] = None
    occurred_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentDetail(DocumentSummary):
    description: Optional[str] = None
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    content_hash: Optional[str] = None
    size_bytes: Optional[int] = None
    language: Optional[str] = None
    access_level: Optional[str] = None
    license_terms: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    entity_links: List[DocumentEntityLinkResponse] = Field(default_factory=list)


class DocumentListResponse(BaseModel):
    items: List[DocumentSummary]
    total: int
    limit: int
    offset: int


# --- Claims ---


class ClaimEntityLinkInput(BaseModel):
    entity_id: str = Field(..., min_length=1, max_length=36)
    relevance: Optional[str] = Field(default=None, max_length=100)


class ClaimEntityLinkResponse(ClaimEntityLinkInput):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    created_at: datetime


class ClaimCreate(BaseModel):
    claim_text: str = Field(..., min_length=1)
    claim_type: Optional[str] = Field(default="declaracao", max_length=50)
    claim_origin: Optional[str] = Field(default="manual", max_length=50)
    verification_status: Optional[str] = Field(default="nao_verificado", max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    justification: Optional[str] = None
    source_id: Optional[str] = Field(default=None, max_length=36)
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    document_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)
    entity_ids: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    occurred_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    structured_json: Optional[Dict[str, Any]] = None
    metadata_json: Optional[Dict[str, Any]] = None


class ClaimUpdate(BaseModel):
    claim_text: Optional[str] = Field(default=None, min_length=1)
    claim_type: Optional[str] = Field(default=None, max_length=50)
    verification_status: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    justification: Optional[str] = None
    source_id: Optional[str] = Field(default=None, max_length=36)
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    document_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)
    entity_ids: Optional[List[str]] = None
    published_at: Optional[datetime] = None
    occurred_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    structured_json: Optional[Dict[str, Any]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    conflict_status: Optional[str] = Field(default=None, max_length=50)


class ClaimSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_text: str
    claim_type: str
    claim_origin: str
    verification_status: str
    conflict_status: str
    confidence: Optional[float] = None
    entity_id: Optional[str] = None
    source_id: Optional[str] = None
    document_id: Optional[str] = None
    research_source_id: Optional[str] = None
    raw_record_id: Optional[str] = None
    occurred_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class EvidenceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    evidence_type: Optional[str] = None
    relation_type: str
    document_id: Optional[str] = None
    research_source_id: Optional[str] = None
    source_id: Optional[str] = None
    raw_record_id: Optional[str] = None
    locator: Optional[str] = None
    snippet: Optional[str] = None
    excerpt: Optional[str] = None
    verification_status: str
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class ClaimConflictSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim_id: str
    conflicting_claim_id: str
    conflict_type: str
    description: Optional[str] = None
    status: str
    detected_by: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ClaimDetail(ClaimSummary):
    justification: Optional[str] = None
    structured_json: Optional[Dict[str, Any]] = None
    metadata_json: Optional[Dict[str, Any]] = None
    version: int = 1
    supersedes_claim_id: Optional[str] = None
    collected_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    entity_links: List[ClaimEntityLinkResponse] = Field(default_factory=list)
    evidence: List[EvidenceSummary] = Field(default_factory=list)
    conflicts: List[ClaimConflictSummary] = Field(default_factory=list)


class ClaimListResponse(BaseModel):
    items: List[ClaimSummary]
    total: int
    limit: int
    offset: int


# --- Conflicts ---


class ClaimConflictCreate(BaseModel):
    conflicting_claim_id: str = Field(..., min_length=1, max_length=36)
    conflict_type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(default="open", max_length=50)


class ClaimConflictUpdate(BaseModel):
    conflict_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=50)


class ClaimConflictDetail(ClaimConflictSummary):
    pass


class ClaimConflictListResponse(BaseModel):
    items: List[ClaimConflictSummary]
    total: int
    limit: int
    offset: int


# --- Evidence ---

EvidenceRelationType = Literal["supports", "contests", "contextualizes"]


class EvidenceCreate(BaseModel):
    evidence_type: Optional[str] = Field(default=None, max_length=100)
    relation_type: str = Field(default="supports", max_length=50)
    document_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)
    source_id: Optional[str] = Field(default=None, max_length=36)
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    locator: Optional[str] = None
    location_json: Optional[Dict[str, Any]] = None
    snippet: Optional[str] = None
    excerpt: Optional[str] = None
    note: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    verification_status: Optional[str] = Field(default="nao_verificado", max_length=50)


class EvidenceUpdate(BaseModel):
    evidence_type: Optional[str] = Field(default=None, max_length=100)
    relation_type: Optional[str] = Field(default=None, max_length=50)
    document_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)
    source_id: Optional[str] = Field(default=None, max_length=36)
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    locator: Optional[str] = None
    location_json: Optional[Dict[str, Any]] = None
    snippet: Optional[str] = None
    excerpt: Optional[str] = None
    note: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    verification_status: Optional[str] = Field(default=None, max_length=50)


class EvidenceDetail(EvidenceSummary):
    location_json: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None


class EvidenceListResponse(BaseModel):
    items: List[EvidenceSummary]
    total: int
    limit: int
    offset: int


# --- Research Workspace Summary ---


class ResearchSummaryResponse(BaseModel):
    entity_id: str
    documents_count: int
    research_sources_count: int
    claims_count: int
    evidence_count: int
    pending_verification_claims: int
    open_conflicts: int
    claims_by_type: Dict[str, int] = Field(default_factory=dict)
    claims_by_verification: Dict[str, int] = Field(default_factory=dict)
