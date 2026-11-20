from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InteractionCreate(BaseModel):
    interaction_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    nature: str = Field(..., min_length=1, max_length=50)
    status: Optional[str] = Field(default="registered", max_length=50)
    occurred_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    time_precision: Optional[str] = Field(default=None, max_length=30)
    channel: Optional[str] = Field(default=None, max_length=100)
    location_text: Optional[str] = Field(default=None, max_length=300)
    participants_text: Optional[str] = None
    source_locator: Optional[str] = None
    document_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    claim_id: Optional[str] = Field(default=None, max_length=36)
    evidence_id: Optional[str] = Field(default=None, max_length=36)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    justification: Optional[str] = None
    verification_status: Optional[str] = Field(default="nao_verificado", max_length=50)
    metadata_json: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = Field(default=None, max_length=100)


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = None
    nature: Optional[str] = Field(default=None, min_length=1, max_length=50)
    status: Optional[str] = Field(default=None, max_length=50)
    occurred_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    time_precision: Optional[str] = Field(default=None, max_length=30)
    channel: Optional[str] = Field(default=None, max_length=100)
    location_text: Optional[str] = Field(default=None, max_length=300)
    participants_text: Optional[str] = None
    source_locator: Optional[str] = None
    document_id: Optional[str] = Field(default=None, max_length=36)
    research_source_id: Optional[str] = Field(default=None, max_length=36)
    raw_record_id: Optional[str] = Field(default=None, max_length=36)
    claim_id: Optional[str] = Field(default=None, max_length=36)
    evidence_id: Optional[str] = Field(default=None, max_length=36)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    justification: Optional[str] = None
    verification_status: Optional[str] = Field(default=None, max_length=50)
    metadata_json: Optional[Dict[str, Any]] = None


class InteractionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    interaction_type: str
    title: str
    description: Optional[str] = None
    nature: str
    status: str
    occurred_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    time_precision: Optional[str] = None
    channel: Optional[str] = None
    location_text: Optional[str] = None
    verification_status: str
    created_at: datetime
    updated_at: datetime


class InteractionDetail(InteractionSummary):
    participants_text: Optional[str] = None
    source_locator: Optional[str] = None
    document_id: Optional[str] = None
    research_source_id: Optional[str] = None
    raw_record_id: Optional[str] = None
    claim_id: Optional[str] = None
    evidence_id: Optional[str] = None
    confidence: Optional[float] = None
    justification: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class InteractionListResponse(BaseModel):
    items: List[InteractionSummary]
    total: int
    limit: int
    offset: int


class InteractionSummaryResponse(BaseModel):
    entity_id: str
    interactions_count: int
    pending_confirmation_or_review: int
    by_nature: Dict[str, int]
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    earliest_occurred_at: Optional[datetime] = None
    latest_occurred_at: Optional[datetime] = None
