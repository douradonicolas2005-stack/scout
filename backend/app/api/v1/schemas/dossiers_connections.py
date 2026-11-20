from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Directionality = Literal["directed", "undirected"]
Nature = Literal["declarado", "observado", "inferido", "a_confirmar"]
VerificationStatusD4 = Literal["nao_verificado", "verificado", "contestado"]
ConnectionStatus = Literal["active", "needs_review", "inactive", "archived"]
TimePrecision = Literal["exact", "month", "year", "estimated", "unknown"]


class ConnectionEntitySummary(BaseModel):
    id: str
    canonical_name: str
    entity_type: str
    profile_status: Optional[str] = None


class TaxonomyRelationType(BaseModel):
    id: str
    category: str
    name: str
    description: str
    directionality: Directionality
    from_entity_types: List[str]
    to_entity_types: List[str]
    status_mvp: str
    inverse_label: Optional[str] = None
    symmetric_label: Optional[str] = None
    inverse_type_id: Optional[str] = None
    notes: Optional[str] = None


class ConnectionCreate(BaseModel):
    relation_type: str = Field(..., min_length=1, max_length=100)
    # directed: prefer explicit from_entity_id/to_entity_id; alternatively other_entity_id + anchor_role
    from_entity_id: Optional[str] = Field(default=None, max_length=36)
    to_entity_id: Optional[str] = Field(default=None, max_length=36)
    other_entity_id: Optional[str] = Field(default=None, max_length=36)
    anchor_role: Optional[Literal["from", "to"]] = None
    directionality: Optional[Directionality] = None

    nature: Optional[Nature] = Field(default="declarado")
    verification_status: Optional[VerificationStatusD4] = Field(default="nao_verificado")
    status: Optional[ConnectionStatus] = Field(default="active")

    description: Optional[str] = None
    justification: Optional[str] = None
    source_locator: Optional[str] = None

    occurred_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    time_precision: Optional[TimePrecision] = None

    claim_id: Optional[str] = Field(default=None, max_length=36)
    evidence_id: Optional[str] = Field(default=None, max_length=36)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    attributes_json: Optional[Dict[str, Any]] = None

    created_by: str = Field(..., min_length=3, max_length=100)


class ConnectionUpdate(BaseModel):
    relation_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    from_entity_id: Optional[str] = Field(default=None, max_length=36)
    to_entity_id: Optional[str] = Field(default=None, max_length=36)
    other_entity_id: Optional[str] = Field(default=None, max_length=36)
    anchor_role: Optional[Literal["from", "to"]] = None
    directionality: Optional[Directionality] = None

    nature: Optional[Nature] = None
    verification_status: Optional[VerificationStatusD4] = None
    status: Optional[ConnectionStatus] = None

    description: Optional[str] = None
    justification: Optional[str] = None
    source_locator: Optional[str] = None

    occurred_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    time_precision: Optional[TimePrecision] = None

    claim_id: Optional[str] = Field(default=None, max_length=36)
    evidence_id: Optional[str] = Field(default=None, max_length=36)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    attributes_json: Optional[Dict[str, Any]] = None


class ConnectionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_entity_id: str
    to_entity_id: str
    relation_type: str
    relation_type_name: Optional[str] = None
    category: Optional[str] = None
    directionality: str
    nature: Optional[str] = None
    verification_status: Optional[str] = None
    status: Optional[str] = None
    occurred_at: Optional[datetime] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    time_precision: Optional[str] = None
    confidence: Optional[float] = None
    claim_id: Optional[str] = None
    evidence_id: Optional[str] = None
    source_locator: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    from_entity: Optional[ConnectionEntitySummary] = None
    to_entity: Optional[ConnectionEntitySummary] = None
    # perspective relative to anchor when listed for an entity
    counterpart_entity: Optional[ConnectionEntitySummary] = None
    perspective: Optional[Literal["outgoing", "incoming", "undirected"]] = None
    perspective_label: Optional[str] = None
    has_evidence: bool = False


class ConnectionDetail(ConnectionSummary):
    description: Optional[str] = None
    justification: Optional[str] = None
    attributes_json: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    inverse_label: Optional[str] = None
    symmetric_label: Optional[str] = None
    inverse_type_id: Optional[str] = None


class ConnectionListResponse(BaseModel):
    items: List[ConnectionSummary]
    total: int
    limit: int
    offset: int


class ConnectionSummaryResponse(BaseModel):
    entity_id: str
    connections_count: int
    by_nature: Dict[str, int]
    by_verification_status: Dict[str, int]
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    by_category: Dict[str, int]
    outgoing_count: int
    incoming_count: int
    undirected_count: int
    with_evidence_count: int


class ConnectionTaxonomyResponse(BaseModel):
    items: List[TaxonomyRelationType]
    approved_count: int
    total: int
