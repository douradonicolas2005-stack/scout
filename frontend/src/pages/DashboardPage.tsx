import { useEffect, useState } from "react";
import { CheckCircle2, Database, Server, Shield } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PageState } from "@/components/shared/PageState";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";
import type { DbStatusResponse, HealthResponse, SystemInfoResponse } from "@/lib/api/types";

type DashboardState =
  | { status: "loading" }
  | {
      status: "ready";
      health: HealthResponse;
      system: SystemInfoResponse | null;
      db: DbStatusResponse | null;
      systemError: string | null;
      dbError: string | null;
    }
  | { status: "error"; message: string };

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Falha ao consultar a API.";
}

export function DashboardPage() {
  const [state, setState] = useState<DashboardState>({ status: "loading" });

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const health = await api.health();
        if (!mounted) return;

        const [systemResult, dbResult] = await Promise.allSettled([api.systemInfo(), api.dbStatus()]);
        if (!mounted) return;

        const system = systemResult.status === "fulfilled" ? systemResult.value : null;
        const db = dbResult.status === "fulfilled" ? dbResult.value : null;
        const systemError =
          systemResult.status === "rejected" ? getErrorMessage(systemResult.reason) : null;
        const dbError = dbResult.status === "rejected" ? getErrorMessage(dbResult.reason) : null;

        setState({ status: "ready", health, system, db, systemError, dbError });
      } catch (err) {
        if (!mounted) return;
        setState({ status: "error", message: getErrorMessage(err) });
      }
    }

    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Foundation V1.1"
        description="Infraestrutura local do SCOUT (monólito modular). Esta etapa estabelece base técnica, navegação, design system, banco versionado e contratos — sem inteligência de domínio, previsões, simulações ou funcionalidades completas de módulos."
        icon={<Shield className="h-5 w-5" />}
        badge="Subetapa C concluída"
      />

      {state.status === "loading" && (
        <PageState
          kind="loading"
          title="Conectando ao backend local"
          description="Consultando /api/v1/health, /api/v1/system/info e /api/v1/db/status em loopback..."
        />
      )}

      {state.status === "error" && (
        <PageState
          kind="error"
          title="Backend indisponível"
          description={`Não foi possível obter resposta da API em ${baseUrl}. Verifique se o serviço local está em execução. Detalhe: ${state.message}`}
        />
      )}

      {state.status === "ready" && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Server className="h-4 w-4" aria-hidden="true" /> API local
                </CardDescription>
                <CardTitle className="flex flex-wrap items-center gap-2 text-base">
                  {state.health.service}
                  <Badge variant="secondary">{state.health.status}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted-foreground">
                <div>Versão: <span className="text-foreground">{state.health.version}</span></div>
                <div>Ambiente: <span className="text-foreground">{state.health.environment}</span></div>
                <div>Fase (health): <span className="text-foreground">{state.health.phase}</span></div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Shield className="h-4 w-4" aria-hidden="true" /> Sistema
                </CardDescription>
                <CardTitle className="text-base">Metadados</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted-foreground">
                {state.system ? (
                  <>
                    <div>App: <span className="text-foreground">{state.system.app_name}</span></div>
                    <div>Fase: <span className="text-foreground">{state.system.phase}</span></div>
                    <div>API: <span className="text-foreground">/{state.system.api_version}</span></div>
                    <div>Scheduler: <span className="text-foreground">{String(state.system.scheduler.enabled ?? "n/d")}</span></div>
                  </>
                ) : (
                  <div>Indisponível: <span className="text-foreground">{state.systemError ?? "erro desconhecido"}</span></div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <Database className="h-4 w-4" aria-hidden="true" /> Banco de dados
                </CardDescription>
                <CardTitle className="flex flex-wrap items-center gap-2 text-base">
                  SQLite
                  {state.db ? (
                    <Badge variant={state.db.connected ? "secondary" : "outline"}>
                      {state.db.connected ? "conectado" : "desconectado"}
                    </Badge>
                  ) : null}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1 text-sm text-muted-foreground">
                {state.db ? (
                  <>
                    <div>Tabelas: <span className="text-foreground">{state.db.table_count}</span></div>
                    <div>Revisão: <span className="text-foreground">{state.db.alembic_revision ?? "nenhuma"}</span></div>
                    <div>Journal: <span className="text-foreground">{state.db.journal_mode ?? "n/d"}</span></div>
                    {state.db.error ? <div className="text-destructive">Erro: {state.db.error}</div> : null}
                  </>
                ) : (
                  <div>Indisponível: <span className="text-foreground">{state.dbError ?? "erro desconhecido"}</span></div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> Progresso
                </CardDescription>
                <CardTitle className="text-base">Foundation em consolidação</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Subetapas A, B e C concluídas. Integração de leitura de estado (D) em andamento nesta
                etapa de avaliação. Módulos funcionais permanecem placeholders.
              </CardContent>
            </Card>
          </div>

          {state.system ? (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Áreas funcionais (estado de implementação)</CardTitle>
                <CardDescription>
                  Registro real do backend (`/api/v1/system/info`). Nenhuma funcionalidade de domínio está implementada.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                  {state.system.modules.map((mod) => (
                    <div key={mod.key} className="rounded-md border border-border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">{mod.label}</span>
                        <Badge variant="outline">{mod.status}</Badge>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">{mod.path}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : (
            <PageState
              kind="error"
              title="Metadados do sistema indisponíveis"
              description={`Não foi possível carregar /api/v1/system/info. Detalhe: ${state.systemError ?? "erro desconhecido"}`}
            />
          )}

          <PageState
            kind="info"
            title="Próximas subetapas (aguardando aprovação)"
            description="D: integração frontend-backend (em avaliação). E: Source Registry e conectores. F: scheduler e pipeline. G: Source Manager. H: testes, documentação e validação. Nenhuma funcionalidade de domínio, ingestão real, previsão ou simulação foi implementada."
          />
        </>
      )}
    </div>
  );
}
