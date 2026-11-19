import type {
  CollectionJobCreate,
  CollectionJobListResponse,
  CollectionRunListResponse,
  ConnectorListResponse,
  DbStatusResponse,
  HealthResponse,
  JobExecutionResponse,
  ProcessingEventListResponse,
  SourceListResponse,
  AuditEventListResponse,
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

function qs(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(
    (entry): entry is [string, string] => entry[1] !== undefined && entry[1] !== "",
  );
  if (!entries.length) return "";
  return `?${new URLSearchParams(entries).toString()}`;
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
};

export type ApiClient = typeof api;
