import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bot,
  Clock3,
  Database,
  Play,
  Plug,
  RefreshCw,
  Settings,
  Zap,
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PageState } from "@/components/shared/PageState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api/client";
import type {
  AuditEventResponse,
  CollectionJobResponse,
  CollectionRunResponse,
  ConnectorResponse,
  DbStatusResponse,
  ProcessingEventResponse,
  SourceResponse,
  SourceTestConnectionResponse,
  SystemInfoResponse,
} from "@/lib/api/types";

type SystemState =
  | { status: "loading" }
  | {
      status: "ready";
      info: SystemInfoResponse | null;
      db: DbStatusResponse | null;
      infoError: string | null;
      dbError: string | null;
    };

type IngestionState = {
  loading: boolean;
  loaded: boolean;
  error: string | null;
  connectors: ConnectorResponse[];
  sources: SourceResponse[];
  jobs: CollectionJobResponse[];
};

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Falha ao consultar a API.";
}

function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function statusBadgeVariant(status: string): "default" | "secondary" | "outline" | "accent" {
  const s = status.toLowerCase();
  if (["succeeded", "success", "active", "ok", "registered"].includes(s)) return "secondary";
  if (["running", "pending", "queued"].includes(s)) return "accent";
  if (["failed", "error", "inactive", "disabled", "cancelled", "canceled"].includes(s))
    return "outline";
  return "default";
}

function shortId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 8)}…` : id;
}

export function SystemPage() {
  const [state, setState] = useState<SystemState>({ status: "loading" });
  const [ingestion, setIngestion] = useState<IngestionState>({
    loading: true,
    loaded: false,
    error: null,
    connectors: [],
    sources: [],
    jobs: [],
  });

  const [sourceAction, setSourceAction] = useState<Record<string, "test" | "collect" | null>>({});
  const [jobAction, setJobAction] = useState<Record<string, "run" | null>>({});
  const [actionNotice, setActionNotice] = useState<
    { kind: "success" | "error"; message: string } | null
  >(null);
  const [testResults, setTestResults] = useState<Record<string, SourceTestConnectionResponse>>({});

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [runs, setRuns] = useState<CollectionRunResponse[]>([]);
  const [runsLoading, setRunsLoading] = useState(false);
  const [runsError, setRunsError] = useState<string | null>(null);

  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<ProcessingEventResponse[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsError, setEventsError] = useState<string | null>(null);

  const [executeNow, setExecuteNow] = useState(true);
  const [selectedSourceForJob, setSelectedSourceForJob] = useState<string>("");
  const [creatingJob, setCreatingJob] = useState(false);

  const [auditEvents, setAuditEvents] = useState<AuditEventResponse[]>([]);
  const [auditLoading, setAuditLoading] = useState(true);
  const [auditLoaded, setAuditLoaded] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  const loadSystem = useCallback(async () => {
    const [infoResult, dbResult] = await Promise.allSettled([api.systemInfo(), api.dbStatus()]);
    setState({
      status: "ready",
      info: infoResult.status === "fulfilled" ? infoResult.value : null,
      db: dbResult.status === "fulfilled" ? dbResult.value : null,
      infoError: infoResult.status === "rejected" ? getErrorMessage(infoResult.reason) : null,
      dbError: dbResult.status === "rejected" ? getErrorMessage(dbResult.reason) : null,
    });
  }, []);

  const loadIngestion = useCallback(async () => {
    setIngestion((prev) => ({ ...prev, loading: true, error: null }));
    const [connectorsRes, sourcesRes, jobsRes] = await Promise.allSettled([
      api.listConnectors(),
      api.listSources(),
      api.listJobs(),
    ]);
    const errors: string[] = [];
    const connectors = connectorsRes.status === "fulfilled" ? connectorsRes.value.items : [];
    const sources = sourcesRes.status === "fulfilled" ? sourcesRes.value.items : [];
    const jobs = jobsRes.status === "fulfilled" ? jobsRes.value.items : [];
    if (connectorsRes.status === "rejected")
      errors.push(`Conectores: ${getErrorMessage(connectorsRes.reason)}`);
    if (sourcesRes.status === "rejected")
      errors.push(`Fontes: ${getErrorMessage(sourcesRes.reason)}`);
    if (jobsRes.status === "rejected") errors.push(`Jobs: ${getErrorMessage(jobsRes.reason)}`);
    setIngestion({
      loading: false,
      loaded: true,
      error: errors.length ? errors.join(" | ") : null,
      connectors,
      sources,
      jobs,
    });
    setSelectedSourceForJob((prev) => {
      if (prev && sources.some((s) => s.id === prev)) return prev;
      return sources[0]?.id ?? "";
    });
  }, []);

  const loadAudit = useCallback(async () => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      const res = await api.listAuditEvents(30);
      setAuditEvents(res.items);
      setAuditLoaded(true);
    } catch (err) {
      setAuditError(getErrorMessage(err));
      setAuditEvents([]);
      setAuditLoaded(true);
    } finally {
      setAuditLoading(false);
    }
  }, []);

  const loadRuns = useCallback(async (jobId: string) => {
    setRunsLoading(true);
    setRunsError(null);
    try {
      const res = await api.listJobRuns(jobId);
      setRuns(res.items);
    } catch (err) {
      setRunsError(getErrorMessage(err));
      setRuns([]);
    } finally {
      setRunsLoading(false);
    }
  }, []);

  const loadEvents = useCallback(async (runId: string) => {
    setEventsLoading(true);
    setEventsError(null);
    try {
      const res = await api.listRunEvents(runId);
      setEvents(res.items);
    } catch (err) {
      setEventsError(getErrorMessage(err));
      setEvents([]);
    } finally {
      setEventsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSystem();
  }, [loadSystem]);

  useEffect(() => {
    void loadIngestion();
  }, [loadIngestion]);

  useEffect(() => {
    void loadAudit();
  }, [loadAudit]);

  useEffect(() => {
    if (!selectedJobId) {
      setRuns([]);
      setRunsError(null);
      return;
    }
    void loadRuns(selectedJobId);
  }, [selectedJobId, loadRuns]);

  useEffect(() => {
    if (!selectedRunId) {
      setEvents([]);
      setEventsError(null);
      return;
    }
    void loadEvents(selectedRunId);
  }, [selectedRunId, loadEvents]);

  const selectedJob = useMemo(
    () => ingestion.jobs.find((j) => j.id === selectedJobId) ?? null,
    [ingestion.jobs, selectedJobId],
  );

  async function handleRefreshAll() {
    setActionNotice(null);
    await Promise.all([loadSystem(), loadIngestion(), loadAudit()]);
    if (selectedJobId) await loadRuns(selectedJobId);
    if (selectedRunId) await loadEvents(selectedRunId);
  }

  async function handleTestSource(sourceId: string) {
    setActionNotice(null);
    setSourceAction((prev) => ({ ...prev, [sourceId]: "test" }));
    try {
      const result = await api.testSourceConnection(sourceId);
      setTestResults((prev) => ({ ...prev, [sourceId]: result }));
      setActionNotice({
        kind: result.ok ? "success" : "error",
        message: `Teste de conexão (${shortId(sourceId)}): ${result.message}`,
      });
      await Promise.all([loadIngestion(), loadAudit()]);
    } catch (err) {
      setActionNotice({ kind: "error", message: `Falha no teste: ${getErrorMessage(err)}` });
    } finally {
      setSourceAction((prev) => ({ ...prev, [sourceId]: null }));
    }
  }

  async function handleCreateJob(sourceId: string, now: boolean) {
    if (!sourceId) return;
    setActionNotice(null);
    setSourceAction((prev) => ({ ...prev, [sourceId]: "collect" }));
    setCreatingJob(true);
    try {
      const res = await api.createJob({
        source_id: sourceId,
        trigger: "manual-ui",
        requested_by: "system-ui",
        execute_now: now,
      });
      const runInfo = res.run ? ` · run ${res.run.status}` : " · sem execução imediata";
      setActionNotice({
        kind:
          res.run && res.run.status !== "succeeded" && res.run.status !== "running"
            ? "error"
            : "success",
        message: `Job criado (${shortId(res.job.id)}, ${res.job.status})${runInfo}.`,
      });
      await Promise.all([loadIngestion(), loadAudit()]);
      setSelectedJobId(res.job.id);
      if (res.run) {
        setSelectedRunId(res.run.id);
      } else {
        setSelectedRunId(null);
      }
    } catch (err) {
      setActionNotice({
        kind: "error",
        message: `Falha ao criar/executar job: ${getErrorMessage(err)}`,
      });
    } finally {
      setCreatingJob(false);
      setSourceAction((prev) => ({ ...prev, [sourceId]: null }));
    }
  }

  async function handleRunJob(jobId: string) {
    setActionNotice(null);
    setJobAction((prev) => ({ ...prev, [jobId]: "run" }));
    try {
      const res = await api.runJob(jobId);
      const run = res.run;
      setActionNotice({
        kind: run && run.status === "succeeded" ? "success" : "error",
        message: run
          ? `Execução do job ${shortId(jobId)}: run ${run.status}${run.error_message ? ` — ${run.error_message}` : ""}.`
          : `Execução do job ${shortId(jobId)} solicitada, mas nenhum run foi retornado.`,
      });
      await Promise.all([loadIngestion(), loadAudit()]);
      setSelectedJobId(jobId);
      if (run) setSelectedRunId(run.id);
      await loadRuns(jobId);
    } catch (err) {
      setActionNotice({ kind: "error", message: `Falha ao executar job: ${getErrorMessage(err)}` });
    } finally {
      setJobAction((prev) => ({ ...prev, [jobId]: null }));
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="System"
        description="Estado da plataforma e monitoramento operacional real de ingestão (fontes, conectores, jobs, runs, eventos e auditoria). Controles mínimos suportados pelo backend; sem simulações, sem inferência automática e sem módulos funcionais de domínio."
        icon={<Settings className="h-5 w-5" />}
        badge="Foundation G"
        actions={
          <Button variant="outline" size="sm" onClick={() => void handleRefreshAll()}>
            <RefreshCw className="h-4 w-4" /> Atualizar
          </Button>
        }
      />

      {actionNotice && (
        <div
          role="status"
          className={`rounded-md border p-3 text-sm ${
            actionNotice.kind === "success"
              ? "border-primary/30 bg-primary/5 text-foreground"
              : "border-destructive/40 bg-destructive/5 text-destructive"
          }`}
        >
          {actionNotice.message}
        </div>
      )}

      {state.status === "loading" && (
        <PageState
          kind="loading"
          title="Carregando estado do sistema"
          description="Consultando /api/v1/system/info e /api/v1/db/status..."
        />
      )}

      {state.status === "ready" && (
        <>
          {!state.info && (
            <PageState
              kind="error"
              title="Informações do sistema indisponíveis"
              description={`Não foi possível carregar /api/v1/system/info. Detalhe: ${state.infoError ?? "erro desconhecido"}`}
            />
          )}

          {state.info && (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription className="flex items-center gap-2">
                    <Settings className="h-4 w-4" aria-hidden="true" /> Plataforma
                  </CardDescription>
                  <CardTitle className="text-base">{state.info.app_name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm text-muted-foreground">
                  <div>Versão: <span className="text-foreground">{state.info.version}</span></div>
                  <div>Fase: <span className="text-foreground">{state.info.phase}</span></div>
                  <div>Ambiente: <span className="text-foreground">{state.info.environment}</span></div>
                  <div>API: <span className="text-foreground">/{state.info.api_version}</span> · docs <span className="text-foreground">{state.info.docs_url}</span></div>
                  <div>Banco: <span className="text-foreground">{state.info.database}</span></div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription className="flex items-center gap-2">
                    <Bot className="h-4 w-4" aria-hidden="true" /> Inteligência local e scheduler
                  </CardDescription>
                  <CardTitle className="text-base">Configuração (somente leitura)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 text-sm text-muted-foreground">
                  <div>Ollama URL: <span className="text-foreground break-all">{state.info.ollama.base_url ?? "n/d"}</span></div>
                  <div>Modelo ref.: <span className="text-foreground">{state.info.ollama.model ?? "n/d"}</span></div>
                  <div>Modo: <span className="text-foreground">{state.info.ollama.mode ?? "n/d"}</span></div>
                  <div className="flex items-center gap-2">
                    <Clock3 className="h-3.5 w-3.5" aria-hidden="true" />
                    Scheduler habilitado: <span className="text-foreground">{String(state.info.scheduler.enabled ?? "n/d")}</span>
                  </div>
                  <div>Concorrência máx.: <span className="text-foreground">{String(state.info.scheduler.max_concurrent_jobs ?? "n/d")}</span></div>
                  <div>Estado: <span className="text-foreground">{String(state.info.scheduler.state ?? "n/d")}</span></div>
                </CardContent>
              </Card>
            </div>
          )}

          {!state.db && (
            <PageState
              kind="error"
              title="Estado do banco indisponível"
              description={`Não foi possível carregar /api/v1/db/status. Detalhe: ${state.dbError ?? "erro desconhecido"}`}
            />
          )}

          {state.db && (
            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Database className="h-4 w-4" aria-hidden="true" /> Banco de dados
                </CardDescription>
                <CardTitle className="flex flex-wrap items-center gap-2 text-base">
                  {state.db.dialect} ({state.db.table_count} tabelas)
                  <Badge variant={state.db.connected ? "secondary" : "outline"}>
                    {state.db.connected ? "conectado" : "desconectado"}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <div className="grid gap-x-4 gap-y-1 sm:grid-cols-2 lg:grid-cols-3">
                  <div>Revisão Alembic: <span className="text-foreground">{state.db.alembic_revision ?? "nenhuma"}</span></div>
                  <div>Revisões: <span className="text-foreground">{state.db.alembic_revisions.length ? state.db.alembic_revisions.join(", ") : "nenhuma"}</span></div>
                  <div>foreign_keys: <span className="text-foreground">{state.db.foreign_keys ?? "n/d"}</span></div>
                  <div>journal_mode: <span className="text-foreground">{state.db.journal_mode ?? "n/d"}</span></div>
                  <div>busy_timeout: <span className="text-foreground">{state.db.busy_timeout ?? "n/d"}</span></div>
                  <div className="sm:col-span-2 lg:col-span-3 break-all">URL: <span className="text-foreground">{state.db.database_url}</span></div>
                </div>
                {state.db.error ? (
                  <div className="rounded-md border border-destructive/40 bg-destructive/5 p-2 text-destructive">
                    Erro reportado pelo backend: {state.db.error}
                  </div>
                ) : null}
              </CardContent>
            </Card>
          )}
        </>
      )}

      <div className="pt-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          <Plug className="h-5 w-5 text-primary" aria-hidden="true" /> Source Manager e monitoramento de ingestão
        </h2>
        <p className="text-sm text-muted-foreground">
          Dados reais do backend (conectores, fontes, jobs, runs, eventos de processamento e auditoria). Controles disponíveis: testar conexão, criar/executar job e inspecionar histórico/erros.
        </p>
      </div>

      {ingestion.loading && !ingestion.loaded && (
        <PageState kind="loading" title="Carregando dados de ingestão" description="Consultando conectores, fontes e jobs..." />
      )}

      {ingestion.error && (
        <PageState
          kind="error"
          title="Falha parcial ou total ao carregar ingestão"
          description={ingestion.error}
        />
      )}

      {ingestion.loaded && (
        <div className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Plug className="h-4 w-4" aria-hidden="true" /> Conectores registrados
                </CardDescription>
                <CardTitle className="text-base">{ingestion.connectors.length} conector(es)</CardTitle>
              </CardHeader>
              <CardContent>
                {ingestion.connectors.length === 0 ? (
                  <PageState kind="empty" title="Nenhum conector" description="Nenhum conector registrado/sincronizado no momento." />
                ) : (
                  <div className="space-y-2">
                    {ingestion.connectors.map((c) => (
                      <div key={c.id} className="rounded-md border border-border p-3 text-sm">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="font-medium text-foreground">{c.name} <span className="font-mono text-xs text-muted-foreground">({c.key})</span></div>
                          <Badge variant={statusBadgeVariant(c.status)}>{c.status}</Badge>
                        </div>
                        <div className="mt-1 text-muted-foreground">Versão: {c.version ?? "n/d"} · Atualizado: {fmtDate(c.updated_at)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Activity className="h-4 w-4" aria-hidden="true" /> Criar job de coleta
                </CardDescription>
                <CardTitle className="text-base">Controle mínimo (manual)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {ingestion.sources.length === 0 ? (
                  <PageState kind="empty" title="Nenhuma fonte disponível" description="Cadastre uma fonte (via API/etapas anteriores) para criar jobs de coleta." />
                ) : (
                  <>
                    <label className="block space-y-1">
                      <span className="text-muted-foreground">Fonte</span>
                      <select
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        value={selectedSourceForJob}
                        onChange={(e) => setSelectedSourceForJob(e.target.value)}
                      >
                        {ingestion.sources.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.name} ({s.connection_type}){!s.is_active ? " [inativa]" : ""}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="flex items-center gap-2 text-muted-foreground">
                      <input
                        type="checkbox"
                        checked={executeNow}
                        onChange={(e) => setExecuteNow(e.target.checked)}
                      />
                      Executar imediatamente (execute_now)
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        onClick={() => void handleCreateJob(selectedSourceForJob, executeNow)}
                        disabled={!selectedSourceForJob || creatingJob}
                      >
                        <Zap className="h-4 w-4" /> {creatingJob ? "Criando..." : executeNow ? "Criar e executar" : "Criar (pendente)"}
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Execução respeita pipeline/conector reais e rastreabilidade no banco. Scheduler pode permanecer desabilitado; jobs pendentes elegíveis são despachados quando habilitado.
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2">
                <Database className="h-4 w-4" aria-hidden="true" /> Fontes (Source Registry)
              </CardDescription>
              <CardTitle className="text-base">{ingestion.sources.length} fonte(s)</CardTitle>
            </CardHeader>
            <CardContent>
              {ingestion.sources.length === 0 ? (
                <PageState kind="empty" title="Nenhuma fonte cadastrada" description="Não há fontes no registry. Use a API para cadastrar fontes (ex.: POST /api/v1/ingestion/sources)." />
              ) : (
                <div className="space-y-3">
                  {ingestion.sources.map((s) => {
                    const busy = sourceAction[s.id];
                    const test = testResults[s.id];
                    return (
                      <div key={s.id} className="rounded-md border border-border p-3 text-sm">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <div className="space-y-1 min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-medium text-foreground">{s.name}</span>
                              <Badge variant={statusBadgeVariant(s.status)}>{s.status}</Badge>
                              <Badge variant={s.is_active ? "secondary" : "outline"}>{s.is_active ? "ativa" : "inativa"}</Badge>
                              <span className="font-mono text-xs text-muted-foreground">{shortId(s.id)}</span>
                            </div>
                            <div className="text-muted-foreground break-all">Locator: <span className="text-foreground">{s.resource_locator}</span></div>
                            <div className="text-muted-foreground">Conector: <span className="text-foreground">{s.connection_type}</span> · Categoria: <span className="text-foreground">{s.category ?? "n/d"}</span></div>
                            <div className="text-muted-foreground">Última coleta: <span className="text-foreground">{fmtDate(s.last_collected_at)}</span> · Atualizada: <span className="text-foreground">{fmtDate(s.updated_at)}</span></div>
                          </div>
                          <div className="flex flex-wrap gap-2 shrink-0">
                            <Button variant="outline" size="sm" disabled={!!busy} onClick={() => void handleTestSource(s.id)}>
                              <Plug className="h-4 w-4" /> {busy === "test" ? "Testando..." : "Testar conexão"}
                            </Button>
                            <Button size="sm" disabled={!!busy} onClick={() => void handleCreateJob(s.id, true)}>
                              <Play className="h-4 w-4" /> {busy === "collect" ? "Executando..." : "Coletar agora"}
                            </Button>
                          </div>
                        </div>
                        {test ? (
                          <div className={`mt-2 rounded-md border p-2 text-xs ${test.ok ? "border-primary/30 bg-primary/5" : "border-destructive/40 bg-destructive/5"}`}>
                            <div className="font-medium">Último teste: {test.ok ? "ok" : "falha"} · {fmtDate(test.tested_at)}</div>
                            <div className="text-muted-foreground break-words">{test.message}</div>
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2">
                <Clock3 className="h-4 w-4" aria-hidden="true" /> Jobs de coleta
              </CardDescription>
              <CardTitle className="text-base">{ingestion.jobs.length} job(s) registrados</CardTitle>
            </CardHeader>
            <CardContent>
              {ingestion.jobs.length === 0 ? (
                <PageState kind="empty" title="Nenhum job" description="Ainda não há jobs de coleta. Crie um job para uma fonte para iniciar o pipeline rastreável." />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <caption className="sr-only">Jobs de coleta</caption>
                    <thead className="text-xs uppercase text-muted-foreground">
                      <tr className="border-b border-border">
                        <th className="py-2 pr-3 font-medium">Job</th>
                        <th className="py-2 pr-3 font-medium">Fonte</th>
                        <th className="py-2 pr-3 font-medium">Status</th>
                        <th className="py-2 pr-3 font-medium">Trigger</th>
                        <th className="py-2 pr-3 font-medium">Tentativa</th>
                        <th className="py-2 pr-3 font-medium">Criado</th>
                        <th className="py-2 pr-3 font-medium">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ingestion.jobs.map((j) => {
                        const running = jobAction[j.id] === "run";
                        const selected = selectedJobId === j.id;
                        return (
                          <tr key={j.id} className={`border-b border-border/60 last:border-0 ${selected ? "bg-secondary/30" : ""}`}>
                            <td className="py-2 pr-3 font-mono text-xs text-foreground">{shortId(j.id)}</td>
                            <td className="py-2 pr-3 font-mono text-xs text-muted-foreground">{shortId(j.source_id)}</td>
                            <td className="py-2 pr-3"><Badge variant={statusBadgeVariant(j.status)}>{j.status}</Badge></td>
                            <td className="py-2 pr-3 text-muted-foreground">{j.trigger}</td>
                            <td className="py-2 pr-3 text-muted-foreground">{j.attempt}/{j.max_attempts}</td>
                            <td className="py-2 pr-3 text-muted-foreground whitespace-nowrap">{fmtDate(j.created_at)}</td>
                            <td className="py-2 pr-3">
                              <div className="flex flex-wrap gap-2">
                                <Button variant={selected ? "secondary" : "outline"} size="sm" onClick={() => { setSelectedJobId(j.id); setSelectedRunId(null); }}>
                                  Runs
                                </Button>
                                <Button size="sm" disabled={running} onClick={() => void handleRunJob(j.id)}>
                                  <Play className="h-4 w-4" /> {running ? "..." : "Executar"}
                                </Button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              {ingestion.jobs.some((j) => j.error_summary) && (
                <div className="mt-3 space-y-1">
                  {ingestion.jobs.filter((j) => j.error_summary).slice(0, 5).map((j) => (
                    <div key={j.id} className="rounded-md border border-destructive/40 bg-destructive/5 p-2 text-xs text-destructive">
                      Job {shortId(j.id)}: {j.error_summary}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {selectedJob && (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Histórico de runs</CardDescription>
                  <CardTitle className="text-base">Job {shortId(selectedJob.id)}</CardTitle>
                </CardHeader>
                <CardContent>
                  {runsLoading && <PageState kind="loading" title="Carregando runs" description="Consultando histórico do job..." />}
                  {runsError && <PageState kind="error" title="Erro ao carregar runs" description={runsError} />}
                  {!runsLoading && !runsError && runs.length === 0 && (
                    <PageState kind="empty" title="Sem runs" description="Este job ainda não possui runs registrados." />
                  )}
                  {!runsLoading && !runsError && runs.length > 0 && (
                    <div className="space-y-2">
                      {runs.map((r) => (
                        <button
                          key={r.id}
                          type="button"
                          className={`w-full rounded-md border p-3 text-left text-sm transition-colors hover:bg-secondary/40 ${selectedRunId === r.id ? "border-primary/40 bg-secondary/30" : "border-border"}`}
                          onClick={() => setSelectedRunId(r.id)}
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-mono text-xs text-foreground">run #{r.run_number} · {shortId(r.id)}</span>
                            <Badge variant={statusBadgeVariant(r.status)}>{r.status}</Badge>
                          </div>
                          <div className="mt-1 text-muted-foreground">
                            encontrados: {r.items_found} · armazenados: {r.items_stored} · dedup: {r.items_deduplicated} · inválidos: {r.items_invalid}
                          </div>
                          <div className="text-xs text-muted-foreground">Início: {fmtDate(r.started_at)} · Fim: {fmtDate(r.finished_at)}</div>
                          {r.error_message ? <div className="mt-1 text-xs text-destructive break-words">{r.error_message}</div> : null}
                        </button>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardDescription>Eventos de processamento</CardDescription>
                  <CardTitle className="text-base">{selectedRunId ? `Run ${shortId(selectedRunId)}` : "Selecione um run"}</CardTitle>
                </CardHeader>
                <CardContent>
                  {!selectedRunId && (
                    <PageState kind="info" title="Nenhum run selecionado" description="Selecione um run para inspecionar eventos/estágios e erros." />
                  )}
                  {selectedRunId && eventsLoading && <PageState kind="loading" title="Carregando eventos" description="Consultando processing_events do run..." />}
                  {selectedRunId && eventsError && <PageState kind="error" title="Erro ao carregar eventos" description={eventsError} />}
                  {selectedRunId && !eventsLoading && !eventsError && events.length === 0 && (
                    <PageState kind="empty" title="Sem eventos" description="Nenhum evento registrado para este run." />
                  )}
                  {selectedRunId && !eventsLoading && !eventsError && events.length > 0 && (
                    <div className="space-y-2 max-h-[28rem] overflow-auto pr-1">
                      {events.map((ev) => (
                        <div key={ev.id} className="rounded-md border border-border p-2 text-xs">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-foreground">{ev.stage}</span>
                            <Badge variant={statusBadgeVariant(ev.status)}>{ev.status}</Badge>
                          </div>
                          <div className="text-muted-foreground">{fmtDate(ev.created_at)}{ev.duration_ms != null ? ` · ${ev.duration_ms}ms` : ""}</div>
                          {ev.message ? <div className="mt-1 break-words text-foreground">{ev.message}</div> : null}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          <Card>
            <CardHeader className="pb-2">
              <CardDescription className="flex items-center gap-2">
                <Activity className="h-4 w-4" aria-hidden="true" /> Auditoria (eventos recentes)
              </CardDescription>
              <CardTitle className="text-base">Rastreabilidade de operações</CardTitle>
            </CardHeader>
            <CardContent>
              {auditLoading && !auditLoaded && (
                <PageState kind="loading" title="Carregando auditoria" description="Consultando /api/v1/system/audit-events..." />
              )}
              {auditError && (
                <PageState kind="error" title="Erro ao carregar auditoria" description={auditError} />
              )}
              {auditLoaded && !auditError && auditEvents.length === 0 && (
                <PageState kind="empty" title="Sem eventos de auditoria" description="Nenhum audit_event registrado até o momento." />
              )}
              {auditLoaded && !auditError && auditEvents.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <caption className="sr-only">Eventos de auditoria recentes</caption>
                    <thead className="text-xs uppercase text-muted-foreground">
                      <tr className="border-b border-border">
                        <th className="py-2 pr-3 font-medium">Quando</th>
                        <th className="py-2 pr-3 font-medium">Ação</th>
                        <th className="py-2 pr-3 font-medium">Severidade</th>
                        <th className="py-2 pr-3 font-medium">Alvo</th>
                        <th className="py-2 pr-3 font-medium">Ator</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditEvents.map((ev) => (
                        <tr key={ev.id} className="border-b border-border/60 last:border-0 align-top">
                          <td className="py-2 pr-3 whitespace-nowrap text-muted-foreground">{fmtDate(ev.created_at)}</td>
                          <td className="py-2 pr-3 text-foreground">{ev.action}</td>
                          <td className="py-2 pr-3"><Badge variant={statusBadgeVariant(ev.severity)}>{ev.severity}</Badge></td>
                          <td className="py-2 pr-3 text-muted-foreground font-mono text-xs break-all">{ev.target_type ? `${ev.target_type}:${ev.target_id ?? "—"}` : "—"}</td>
                          <td className="py-2 pr-3 text-muted-foreground">{ev.actor_type}{ev.actor_id ? `:${ev.actor_id}` : ""}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
