from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.knowledge.provenance import ClaimType, VerificationStatus


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class Connector(Base, TimestampMixin):
    __tablename__ = "connectors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    capabilities_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    config_schema_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="registered")


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_locator: Mapped[str] = mapped_column(Text, nullable=False)
    connection_type: Mapped[str] = mapped_column(String(100), nullable=False)
    auth_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    auth_credential_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="inactive", index=True)
    last_collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_collect_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    config_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    permissions_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    terms_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class CollectionJob(Base):
    __tablename__ = "collection_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    requested_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class CollectionRun(Base):
    __tablename__ = "collection_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("collection_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running", index=True)
    items_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_stored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_deduplicated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_invalid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bytes_downloaded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metrics_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class RawRecord(Base):
    __tablename__ = "raw_records"
    __table_args__ = (
        Index("ix_raw_records_source_external", "source_id", "external_id"),
        Index("ix_raw_records_source_hash", "source_id", "content_hash"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("collection_runs.id", ondelete="SET NULL"), index=True
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_preserved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    license_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    source_locator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value
    )


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    raw_record_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("raw_records.id", ondelete="SET NULL"), index=True
    )
    research_source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("research_sources.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    origin_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_locator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value
    )
    access_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    license_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_reference_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class ExtractedClaim(Base, TimestampMixin):
    __tablename__ = "extracted_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    entity_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    research_source_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("research_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    raw_record_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("raw_records.id", ondelete="SET NULL"), index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), index=True
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    structured_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    claim_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ClaimType.DECLARACAO.value, index=True
    )
    claim_origin: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value
    )
    conflict_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="none", index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    supersedes_claim_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("extracted_claims.id", ondelete="SET NULL"), nullable=True
    )
    registered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("extracted_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    raw_record_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("raw_records.id", ondelete="SET NULL"), index=True
    )
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    research_source_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("research_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evidence_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="supports", index=True
    )
    locator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value
    )


class Entity(Base, TimestampMixin):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # D1
    profile_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # D1
    primary_location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)  # D1
    profile_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)  # D1
    attributes_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value
    )
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source_first_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )


class EntityIdentifier(Base, TimestampMixin):
    __tablename__ = "entity_identifiers"
    __table_args__ = (Index("ix_entity_identifiers_type_norm", "id_type", "normalized_value"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    id_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)


class EntityAlias(Base, TimestampMixin):
    __tablename__ = "entity_aliases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    alias_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


# --- Dossiers D2: Research & Evidence ---


class ResearchSource(Base, TimestampMixin):
    __tablename__ = "research_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    consulted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )
    reliability_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="nao_avaliada", index=True
    )
    reliability_justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value, index=True
    )
    ingestion_source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class DocumentEntityLink(Base):
    __tablename__ = "document_entity_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class ClaimEntityLink(Base):
    __tablename__ = "claim_entity_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("extracted_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relevance: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )


class ClaimConflict(Base, TimestampMixin):
    __tablename__ = "claim_conflicts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    claim_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("extracted_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conflicting_claim_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("extracted_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conflict_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open", index=True)
    detected_by: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


# --- Dossiers D3: Relationship History ---


class EntityInteraction(Base, TimestampMixin):
    __tablename__ = "entity_interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    interaction_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nature: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="registered", index=True
    )
    occurred_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    time_precision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_text: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    participants_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_locator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    research_source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("research_sources.id", ondelete="SET NULL"), nullable=True
    )
    raw_record_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("raw_records.id", ondelete="SET NULL"), nullable=True
    )
    claim_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("extracted_claims.id", ondelete="SET NULL"), nullable=True
    )
    evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value
    )
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class Relationship(Base, TimestampMixin):
    __tablename__ = "relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    from_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    directionality: Mapped[str] = mapped_column(
        String(20), nullable=False, default="directed"
    )
    attributes_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    claim_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("extracted_claims.id", ondelete="SET NULL"), nullable=True
    )
    evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nature: Mapped[str] = mapped_column(String(30), nullable=False, default="declarado")
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=VerificationStatus.NAO_VERIFICADO.value
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active", index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_locator: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    time_precision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class DataChange(Base):
    __tablename__ = "data_changes"
    __table_args__ = (Index("ix_data_changes_entity", "entity_table", "entity_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_table: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    before_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    after_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("collection_runs.id", ondelete="SET NULL"), nullable=True
    )
    processing_event_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    actor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class ProcessingEvent(Base):
    __tablename__ = "processing_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("collection_jobs.id", ondelete="SET NULL"), index=True
    )
    run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("collection_runs.id", ondelete="SET NULL"), index=True
    )
    stage: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    agent_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="ollama")
    model_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    input_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    token_usage_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    requested_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    actor_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    details_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_or_origin: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
