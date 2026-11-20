from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class EntityIdentifierInput(BaseModel):
    id_type: str = Field(default="external_id", min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=500)
    is_primary: bool = False
    metadata_json: Optional[Dict[str, Any]] = None


class EntityIdentifierResponse(EntityIdentifierInput):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    normalized_value: str
    created_at: datetime
    updated_at: datetime


class EntityAliasInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    alias_type: Optional[str] = Field(default=None, max_length=100)


class EntityAliasResponse(EntityAliasInput):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_id: str
    normalized_name: str
    created_at: datetime
    updated_at: datetime


class EntityBase(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=100)
    canonical_name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    profile_status: Optional[str] = Field(default="active", max_length=50)
    primary_location: Optional[str] = Field(default=None, max_length=300)
    verification_status: Optional[str] = Field(default="nao_verificado", max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    profile_data: Optional[Dict[str, Any]] = None
    attributes_json: Optional[Dict[str, Any]] = None
    source_first_id: Optional[str] = Field(default=None, max_length=36)
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class EntityCreate(EntityBase):
    identifiers: List[EntityIdentifierInput] = Field(default_factory=list)
    aliases: List[EntityAliasInput] = Field(default_factory=list)


class EntityUpdate(BaseModel):
    entity_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    canonical_name: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    profile_status: Optional[str] = Field(default=None, max_length=50)
    primary_location: Optional[str] = Field(default=None, max_length=300)
    verification_status: Optional[str] = Field(default=None, max_length=50)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    profile_data: Optional[Dict[str, Any]] = None
    attributes_json: Optional[Dict[str, Any]] = None
    source_first_id: Optional[str] = Field(default=None, max_length=36)
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    identifiers: Optional[List[EntityIdentifierInput]] = None
    aliases: Optional[List[EntityAliasInput]] = None


class EntitySummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_type: str
    canonical_name: str
    normalized_name: str
    description: Optional[str] = None
    profile_status: str
    primary_location: Optional[str] = None
    verification_status: str
    confidence: Optional[float] = None
    source_first_id: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class EntityDetailResponse(EntitySummaryResponse):
    profile_data: Optional[Dict[str, Any]] = None
    attributes_json: Optional[Dict[str, Any]] = None
    identifiers: List[EntityIdentifierResponse] = Field(default_factory=list)
    aliases: List[EntityAliasResponse] = Field(default_factory=list)


class EntityListResponse(BaseModel):
    items: List[EntitySummaryResponse]
    total: int
    limit: int
    offset: int


class DuplicateCandidate(BaseModel):
    candidate: EntitySummaryResponse
    score_level: Literal["high", "medium", "low"]
    reasons: List[str]


class DuplicateCandidatesResponse(BaseModel):
    entity_id: str
    items: List[DuplicateCandidate]
