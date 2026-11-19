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
