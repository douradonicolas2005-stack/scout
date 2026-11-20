export type HealthStatus = "ok" | "degraded" | "error";

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  phase: string;
  timestamp: string;
}

export type ModuleImplementationStatus = "placeholder" | "planned" | "in_development" | "implemented";

export interface ModuleStatus {
  key: string;
  label: string;
  path: string;
  status: ModuleImplementationStatus;
  implemented: boolean;
}

export interface SystemInfoResponse {
  app_name: string;
  version: string;
  phase: string;
  environment: string;
  api_version: string;
  docs_url: string;
  openapi_url: string;
  database: "sqlite";
  ollama: Record<string, string | null>;
  scheduler: Record<string, unknown>;
  modules: ModuleStatus[];
  timestamp: string;
}

export interface DbTableStat {
  name: string;
  row_count: number;
}

export interface DbStatusResponse {
  connected: boolean;
  dialect: string;
  database_url: string;
  table_count: number;
  tables: DbTableStat[];
  alembic_revision: string | null;
  alembic_revisions: string[];
  foreign_keys: number | null;
  journal_mode: string | null;
  busy_timeout: number | null;
  error: string | null;
  timestamp: string;
}

export interface ConnectorResponse {
  id: string;
  key: string;
  name: string;
  version: string | null;
  capabilities: Record<string, unknown> | null;
  config_schema: Record<string, unknown> | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ConnectorListResponse {
  items: ConnectorResponse[];
}

export interface SourceResponse {
  id: string;
  name: string;
  category: string | null;
  description: string | null;
  resource_locator: string;
  connection_type: string;
  auth_method: string | null;
  auth_credential_ref: string | null;
  frequency: string | null;
  status: string;
  last_collected_at: string | null;
  next_collect_at: string | null;
  config_json: Record<string, unknown> | null;
  permissions_json: Record<string, unknown> | null;
  terms_conditions: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceListResponse {
  items: SourceResponse[];
}

export interface SourceTestConnectionResponse {
  source_id: string;
  connector_key: string;
  ok: boolean;
  message: string;
  metadata: Record<string, unknown>;
  tested_at: string;
}

export interface CollectionJobCreate {
  source_id: string;
  trigger?: string;
  requested_by?: string | null;
  scheduled_for?: string | null;
  max_attempts?: number;
  execute_now?: boolean;
}

export interface CollectionJobResponse {
  id: string;
  source_id: string;
  trigger: string;
  status: string;
  priority: number;
  scheduled_for: string | null;
  attempt: number;
  max_attempts: number;
  requested_by: string | null;
  cancel_requested: boolean;
  error_summary: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface CollectionJobListResponse {
  items: CollectionJobResponse[];
}

export interface CollectionRunResponse {
  id: string;
  job_id: string;
  source_id: string;
  run_number: number;
  status: string;
  items_found: number;
  items_stored: number;
  items_deduplicated: number;
  items_invalid: number;
  bytes_downloaded: number;
  error_message: string | null;
  metrics_json: Record<string, unknown> | null;
  started_at: string;
  finished_at: string | null;
}

export interface CollectionRunListResponse {
  items: CollectionRunResponse[];
}

export interface ProcessingEventResponse {
  id: string;
  job_id: string | null;
  run_id: string | null;
  stage: string;
  status: string;
  message: string | null;
  payload_json: Record<string, unknown> | null;
  created_at: string;
  duration_ms: number | null;
}

export interface ProcessingEventListResponse {
  items: ProcessingEventResponse[];
}

export interface JobExecutionResponse {
  job: CollectionJobResponse;
  run: CollectionRunResponse | null;
}

export interface AuditEventResponse {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  target_type: string | null;
  target_id: string | null;
  severity: string;
  details_json: Record<string, unknown> | null;
  ip_or_origin: string | null;
  created_at: string;
}

export interface AuditEventListResponse {
  items: AuditEventResponse[];
}

// Dossiers D1
export type DossierEntityType = "person" | "company" | "economic_group" | "institution" | "other" | string;
export type DuplicateScoreLevel = "high" | "medium" | "low";

export interface EntityIdentifierPayload {
  id_type: string;
  value: string;
  is_primary?: boolean;
  metadata_json?: Record<string, unknown> | null;
}

export interface EntityIdentifierResponse extends EntityIdentifierPayload {
  id: string;
  entity_id: string;
  normalized_value: string;
  is_primary: boolean;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface EntityAliasPayload {
  name: string;
  alias_type?: string | null;
}

export interface EntityAliasResponse extends EntityAliasPayload {
  id: string;
  entity_id: string;
  normalized_name: string;
  alias_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface EntityBaseFields {
  entity_type: DossierEntityType;
  canonical_name: string;
  description?: string | null;
  profile_status?: string | null;
  primary_location?: string | null;
  verification_status?: string | null;
  confidence?: number | null;
  profile_data?: Record<string, unknown> | null;
  attributes_json?: Record<string, unknown> | null;
  source_first_id?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
}

export interface EntityCreatePayload extends EntityBaseFields {
  identifiers?: EntityIdentifierPayload[];
  aliases?: EntityAliasPayload[];
}

export interface EntityUpdatePayload extends Partial<EntityBaseFields> {
  identifiers?: EntityIdentifierPayload[];
  aliases?: EntityAliasPayload[];
}

export interface EntitySummary {
  id: string;
  entity_type: DossierEntityType;
  canonical_name: string;
  normalized_name: string;
  description: string | null;
  profile_status: string;
  primary_location: string | null;
  verification_status: string;
  confidence: number | null;
  source_first_id: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EntityDetail extends EntitySummary {
  profile_data: Record<string, unknown> | null;
  attributes_json: Record<string, unknown> | null;
  identifiers: EntityIdentifierResponse[];
  aliases: EntityAliasResponse[];
}

export interface EntityListResponse {
  items: EntitySummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface DuplicateCandidate {
  candidate: EntitySummary;
  score_level: DuplicateScoreLevel;
  reasons: string[];
}

export interface DuplicateCandidatesResponse {
  entity_id: string;
  items: DuplicateCandidate[];
}


// Dossiers D2 - Research & Evidence
export interface ResearchSourceSummary {
  id: string;
  name: string;
  source_type: string;
  domain: string | null;
  url: string | null;
  classification: string | null;
  consulted_at: string | null;
  last_verified_at: string | null;
  reliability_status: string;
  verification_status: string;
  ingestion_source_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchSourceDetail extends ResearchSourceSummary {
  description: string | null;
  reliability_justification: string | null;
  metadata_json: Record<string, unknown> | null;
  created_by: string | null;
}

export interface ResearchSourceCreatePayload {
  name: string;
  source_type: string;
  domain?: string | null;
  url?: string | null;
  description?: string | null;
  classification?: string | null;
  consulted_at?: string | null;
  last_verified_at?: string | null;
  reliability_status?: string | null;
  reliability_justification?: string | null;
  verification_status?: string | null;
  ingestion_source_id?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_by?: string | null;
}

export type ResearchSourceUpdatePayload = Partial<ResearchSourceCreatePayload>;

export interface ResearchSourceListResponse {
  items: ResearchSourceSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentEntityLink {
  id: string;
  document_id: string;
  entity_id: string;
  role: string | null;
  notes: string | null;
  created_at: string;
}

export interface DocumentSummary {
  id: string;
  title: string | null;
  document_type: string | null;
  origin_type: string | null;
  verification_status: string;
  source_id: string | null;
  raw_record_id: string | null;
  research_source_id: string | null;
  source_locator: string | null;
  storage_path: string | null;
  is_reference_only: boolean;
  published_at: string | null;
  occurred_at: string | null;
  captured_at: string | null;
  collected_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DocumentDetail extends DocumentSummary {
  description: string | null;
  mime_type: string | null;
  checksum: string | null;
  content_hash: string | null;
  size_bytes: number | null;
  language: string | null;
  access_level: string | null;
  license_terms: string | null;
  metadata_json: Record<string, unknown> | null;
  entity_links: DocumentEntityLink[];
}

export interface DocumentCreatePayload {
  title?: string | null;
  document_type?: string | null;
  description?: string | null;
  origin_type?: string | null;
  source_locator?: string | null;
  mime_type?: string | null;
  storage_path?: string | null;
  checksum?: string | null;
  content_hash?: string | null;
  size_bytes?: number | null;
  language?: string | null;
  published_at?: string | null;
  occurred_at?: string | null;
  captured_at?: string | null;
  collected_at?: string | null;
  verification_status?: string | null;
  access_level?: string | null;
  license_terms?: string | null;
  is_reference_only?: boolean;
  metadata_json?: Record<string, unknown> | null;
  source_id?: string | null;
  raw_record_id?: string | null;
  research_source_id?: string | null;
  entity_ids?: string[];
  entity_role?: string | null;
}

export type DocumentUpdatePayload = Partial<Omit<DocumentCreatePayload, 'entity_ids' | 'entity_role'>>;

export interface DocumentListResponse {
  items: DocumentSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ClaimEntityLink {
  id: string;
  claim_id: string;
  entity_id: string;
  relevance: string | null;
  created_at: string;
}

export interface EvidenceSummary {
  id: string;
  claim_id: string;
  evidence_type: string | null;
  relation_type: string;
  document_id: string | null;
  research_source_id: string | null;
  source_id: string | null;
  raw_record_id: string | null;
  locator: string | null;
  snippet: string | null;
  excerpt: string | null;
  verification_status: string;
  confidence: number | null;
  created_at: string;
  updated_at: string;
}

export interface EvidenceDetail extends EvidenceSummary {
  location_json: Record<string, unknown> | null;
  note: string | null;
  published_at: string | null;
  collected_at: string | null;
}

export interface EvidenceCreatePayload {
  evidence_type?: string | null;
  relation_type?: string;
  document_id?: string | null;
  research_source_id?: string | null;
  source_id?: string | null;
  raw_record_id?: string | null;
  locator?: string | null;
  location_json?: Record<string, unknown> | null;
  snippet?: string | null;
  excerpt?: string | null;
  note?: string | null;
  published_at?: string | null;
  collected_at?: string | null;
  confidence?: number | null;
  verification_status?: string | null;
}

export type EvidenceUpdatePayload = Partial<EvidenceCreatePayload>;

export interface EvidenceListResponse {
  items: EvidenceSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ClaimConflictSummary {
  id: string;
  claim_id: string;
  conflicting_claim_id: string;
  conflict_type: string;
  description: string | null;
  status: string;
  detected_by: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClaimConflictCreatePayload {
  conflicting_claim_id: string;
  conflict_type: string;
  description?: string | null;
  status?: string | null;
}

export interface ClaimConflictUpdatePayload {
  conflict_type?: string | null;
  description?: string | null;
  status?: string | null;
}

export interface ClaimConflictListResponse {
  items: ClaimConflictSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ClaimSummary {
  id: string;
  claim_text: string;
  claim_type: string;
  claim_origin: string;
  verification_status: string;
  conflict_status: string;
  confidence: number | null;
  entity_id: string | null;
  source_id: string | null;
  document_id: string | null;
  research_source_id: string | null;
  raw_record_id: string | null;
  occurred_at: string | null;
  published_at: string | null;
  registered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClaimDetail extends ClaimSummary {
  justification: string | null;
  structured_json: Record<string, unknown> | null;
  metadata_json: Record<string, unknown> | null;
  version: number;
  supersedes_claim_id: string | null;
  collected_at: string | null;
  valid_from: string | null;
  valid_to: string | null;
  entity_links: ClaimEntityLink[];
  evidence: EvidenceSummary[];
  conflicts: ClaimConflictSummary[];
}

export interface ClaimCreatePayload {
  claim_text: string;
  claim_type?: string | null;
  claim_origin?: string | null;
  verification_status?: string | null;
  confidence?: number | null;
  justification?: string | null;
  source_id?: string | null;
  raw_record_id?: string | null;
  document_id?: string | null;
  research_source_id?: string | null;
  entity_ids?: string[];
  published_at?: string | null;
  collected_at?: string | null;
  occurred_at?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  registered_at?: string | null;
  structured_json?: Record<string, unknown> | null;
  metadata_json?: Record<string, unknown> | null;
}

export type ClaimUpdatePayload = Partial<Omit<ClaimCreatePayload, 'claim_origin'>> & {
  conflict_status?: string | null;
};

export interface ClaimListResponse {
  items: ClaimSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ResearchSummaryResponse {
  entity_id: string;
  documents_count: number;
  research_sources_count: number;
  claims_count: number;
  evidence_count: number;
  pending_verification_claims: number;
  open_conflicts: number;
  claims_by_type: Record<string, number>;
  claims_by_verification: Record<string, number>;
}

// Dossiers D3 - Relationship History
export type InteractionNature = "declarado" | "observado" | "interpretado" | "a_confirmar" | string;

export interface InteractionCreatePayload {
  interaction_type: string;
  title: string;
  description?: string | null;
  nature: string;
  status?: string | null;
  occurred_at?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  time_precision?: string | null;
  channel?: string | null;
  location_text?: string | null;
  participants_text?: string | null;
  source_locator?: string | null;
  document_id?: string | null;
  research_source_id?: string | null;
  raw_record_id?: string | null;
  claim_id?: string | null;
  evidence_id?: string | null;
  confidence?: number | null;
  justification?: string | null;
  verification_status?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_by?: string | null;
}

export type InteractionUpdatePayload = Partial<InteractionCreatePayload>;

export interface InteractionSummary {
  id: string;
  entity_id: string;
  interaction_type: string;
  title: string;
  description: string | null;
  nature: InteractionNature;
  status: string;
  occurred_at: string | null;
  started_at: string | null;
  ended_at: string | null;
  time_precision: string | null;
  channel: string | null;
  location_text: string | null;
  verification_status: string;
  created_at: string;
  updated_at: string;
}

export interface InteractionDetail extends InteractionSummary {
  participants_text: string | null;
  source_locator: string | null;
  document_id: string | null;
  research_source_id: string | null;
  raw_record_id: string | null;
  claim_id: string | null;
  evidence_id: string | null;
  confidence: number | null;
  justification: string | null;
  metadata_json: Record<string, unknown> | null;
  created_by: string | null;
}

export interface InteractionListResponse {
  items: InteractionSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface InteractionSummaryResponse {
  entity_id: string;
  interactions_count: number;
  pending_confirmation_or_review: number;
  by_nature: Record<string, number>;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  earliest_occurred_at: string | null;
  latest_occurred_at: string | null;
}

