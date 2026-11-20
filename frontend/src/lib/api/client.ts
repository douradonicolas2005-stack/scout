import type {
  AuditEventListResponse,
  ClaimConflictCreatePayload,
  ClaimConflictListResponse,
  ClaimConflictSummary,
  ClaimConflictUpdatePayload,
  ClaimCreatePayload,
  ClaimDetail,
  ClaimListResponse,
  ClaimUpdatePayload,
  CollectionJobCreate,
  CollectionJobListResponse,
  CollectionRunListResponse,
  ConnectorListResponse,
  DbStatusResponse,
  DocumentCreatePayload,
  DocumentDetail,
  DocumentListResponse,
  DocumentUpdatePayload,
  DuplicateCandidatesResponse,
  EntityCreatePayload,
  EntityDetail,
  EntityListResponse,
  EntityUpdatePayload,
  EvidenceCreatePayload,
  EvidenceDetail,
  EvidenceListResponse,
  EvidenceUpdatePayload,
  HealthResponse,
  JobExecutionResponse,
  ProcessingEventListResponse,
  ResearchSourceCreatePayload,
  ResearchSourceDetail,
  ResearchSourceListResponse,
  ResearchSourceUpdatePayload,
  ResearchSummaryResponse,
  SourceListResponse,
  SourceTestConnectionResponse,
  SystemInfoResponse,
} from "./types";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const hasBody = init?.body !== undefined && init?.body !== null;
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let message = text || `HTTP ${res.status}`;
    try {
      const parsed = text ? (JSON.parse(text) as { detail?: unknown }) : null;
      if (parsed && typeof parsed.detail === "string") message = parsed.detail;
      else if (parsed && Array.isArray(parsed.detail)) message = JSON.stringify(parsed.detail);
    } catch {
      // keep raw text
    }
    throw new Error(message);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(
    (entry): entry is [string, string | number] => entry[1] !== undefined && entry[1] !== "",
  );
  if (!entries.length) return "";
  return `?${new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()}`;
}

export const api = {
  health: () => request<HealthResponse>("/api/v1/health"),
  systemInfo: () => request<SystemInfoResponse>("/api/v1/system/info"),
  dbStatus: () => request<DbStatusResponse>("/api/v1/db/status"),

  listConnectors: () => request<ConnectorListResponse>("/api/v1/ingestion/connectors"),
  listSources: (activeOnly?: boolean) =>
    request<SourceListResponse>(
      `/api/v1/ingestion/sources${qs({ active_only: activeOnly ? "true" : undefined })}`,
    ),
  testSourceConnection: (sourceId: string) =>
    request<SourceTestConnectionResponse>(
      `/api/v1/ingestion/sources/${encodeURIComponent(sourceId)}/test-connection`,
      { method: "POST" },
    ),

  createJob: (payload: CollectionJobCreate) =>
    request<JobExecutionResponse>("/api/v1/ingestion/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listJobs: (params?: { source_id?: string; status?: string }) =>
    request<CollectionJobListResponse>(
      `/api/v1/ingestion/jobs${qs({ source_id: params?.source_id, status: params?.status })}`,
    ),
  runJob: (jobId: string) =>
    request<JobExecutionResponse>(`/api/v1/ingestion/jobs/${encodeURIComponent(jobId)}/run`, {
      method: "POST",
    }),
  listJobRuns: (jobId: string) =>
    request<CollectionRunListResponse>(
      `/api/v1/ingestion/jobs/${encodeURIComponent(jobId)}/runs`,
    ),
  listRunEvents: (runId: string) =>
    request<ProcessingEventListResponse>(
      `/api/v1/ingestion/runs/${encodeURIComponent(runId)}/events`,
    ),

  listAuditEvents: (limit = 50) =>
    request<AuditEventListResponse>(`/api/v1/system/audit-events${qs({ limit: String(limit) })}`),

  // Dossiers D1
  listEntities: (params?: {
    q?: string;
    entity_type?: string;
    profile_status?: string;
    verification_status?: string;
    sort?: string;
    limit?: number;
    offset?: number;
  }) => request<EntityListResponse>(`/api/v1/dossiers/entities${qs(params ?? {})}`),
  getEntity: (entityId: string) =>
    request<EntityDetail>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}`),
  createEntity: (payload: EntityCreatePayload) =>
    request<EntityDetail>("/api/v1/dossiers/entities", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateEntity: (entityId: string, payload: EntityUpdatePayload) =>
    request<EntityDetail>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listDuplicateCandidates: (entityId: string, limit = 10) =>
    request<DuplicateCandidatesResponse>(
      `/api/v1/dossiers/entities/${encodeURIComponent(entityId)}/duplicate-candidates${qs({ limit })}`,
    ),
  // Dossiers D2 - Research & Evidence
  createResearchSource: (payload: ResearchSourceCreatePayload) =>
    request<ResearchSourceDetail>("/api/v1/dossiers/research-sources", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listResearchSources: (params?: {
    q?: string;
    source_type?: string;
    classification?: string;
    reliability_status?: string;
    verification_status?: string;
    sort?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.source_type) qs.set("source_type", params.source_type);
    if (params?.classification) qs.set("classification", params.classification);
    if (params?.reliability_status) qs.set("reliability_status", params.reliability_status);
    if (params?.verification_status) qs.set("verification_status", params.verification_status);
    if (params?.sort) qs.set("sort", params.sort);
    if (params?.limit != null) qs.set("limit", String(params.limit));
    if (params?.offset != null) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<ResearchSourceListResponse>(`/api/v1/dossiers/research-sources${suffix}`);
  },
  getResearchSource: (sourceId: string) =>
    request<ResearchSourceDetail>(`/api/v1/dossiers/research-sources/${encodeURIComponent(sourceId)}`),
  updateResearchSource: (sourceId: string, payload: ResearchSourceUpdatePayload) =>
    request<ResearchSourceDetail>(`/api/v1/dossiers/research-sources/${encodeURIComponent(sourceId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  createDocument: (entityId: string, payload: DocumentCreatePayload) =>
    request<DocumentDetail>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}/documents`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listEntityDocuments: (entityId: string, params?: {
    q?: string;
    document_type?: string;
    verification_status?: string;
    origin_type?: string;
    sort?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.document_type) qs.set("document_type", params.document_type);
    if (params?.verification_status) qs.set("verification_status", params.verification_status);
    if (params?.origin_type) qs.set("origin_type", params.origin_type);
    if (params?.sort) qs.set("sort", params.sort);
    if (params?.limit != null) qs.set("limit", String(params.limit));
    if (params?.offset != null) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<DocumentListResponse>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}/documents${suffix}`);
  },
  getDocument: (documentId: string) =>
    request<DocumentDetail>(`/api/v1/dossiers/documents/${encodeURIComponent(documentId)}`),
  updateDocument: (documentId: string, payload: DocumentUpdatePayload) =>
    request<DocumentDetail>(`/api/v1/dossiers/documents/${encodeURIComponent(documentId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  createClaim: (entityId: string, payload: ClaimCreatePayload) =>
    request<ClaimDetail>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}/claims`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listEntityClaims: (entityId: string, params?: {
    q?: string;
    claim_type?: string;
    verification_status?: string;
    conflict_status?: string;
    sort?: string;
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.claim_type) qs.set("claim_type", params.claim_type);
    if (params?.verification_status) qs.set("verification_status", params.verification_status);
    if (params?.conflict_status) qs.set("conflict_status", params.conflict_status);
    if (params?.sort) qs.set("sort", params.sort);
    if (params?.limit != null) qs.set("limit", String(params.limit));
    if (params?.offset != null) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<ClaimListResponse>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}/claims${suffix}`);
  },
  getClaim: (claimId: string) =>
    request<ClaimDetail>(`/api/v1/dossiers/claims/${encodeURIComponent(claimId)}`),
  updateClaim: (claimId: string, payload: ClaimUpdatePayload) =>
    request<ClaimDetail>(`/api/v1/dossiers/claims/${encodeURIComponent(claimId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  createClaimConflict: (claimId: string, payload: ClaimConflictCreatePayload) =>
    request<ClaimConflictSummary>(`/api/v1/dossiers/claims/${encodeURIComponent(claimId)}/conflicts`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateClaimConflict: (claimId: string, conflictId: string, payload: ClaimConflictUpdatePayload) =>
    request<ClaimConflictSummary>(`/api/v1/dossiers/claims/${encodeURIComponent(claimId)}/conflicts/${encodeURIComponent(conflictId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  listEntityConflicts: (entityId: string, params?: { status?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.status) qs.set("status", params.status);
    if (params?.limit != null) qs.set("limit", String(params.limit));
    if (params?.offset != null) qs.set("offset", String(params.offset));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return request<ClaimConflictListResponse>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}/conflicts${suffix}`);
  },

  createEvidence: (claimId: string, payload: EvidenceCreatePayload) =>
    request<EvidenceDetail>(`/api/v1/dossiers/claims/${encodeURIComponent(claimId)}/evidence`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listClaimEvidence: (claimId: string) =>
    request<EvidenceListResponse>(`/api/v1/dossiers/claims/${encodeURIComponent(claimId)}/evidence`),
  getEvidence: (evidenceId: string) =>
    request<EvidenceDetail>(`/api/v1/dossiers/evidence/${encodeURIComponent(evidenceId)}`),
  updateEvidence: (evidenceId: string, payload: EvidenceUpdatePayload) =>
    request<EvidenceDetail>(`/api/v1/dossiers/evidence/${encodeURIComponent(evidenceId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  getResearchSummary: (entityId: string) =>
    request<ResearchSummaryResponse>(`/api/v1/dossiers/entities/${encodeURIComponent(entityId)}/research/summary`),

};

export type ApiClient = typeof api;
