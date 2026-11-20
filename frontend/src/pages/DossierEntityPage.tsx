import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, FileText, GitBranch, History, Lightbulb, Pencil, RefreshCw, SearchCheck, UserCircle2 } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PageState } from "@/components/shared/PageState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ResearchWorkspace } from "@/components/dossiers/ResearchWorkspace";
import { api } from "@/lib/api/client";
import type { DuplicateCandidatesResponse, EntityDetail, EntitySummary, EntityUpdatePayload } from "@/lib/api/types";
import {
  ENTITY_TYPE_OPTIONS,
  PROFILE_STATUS_OPTIONS,
  VERIFICATION_OPTIONS,
  aliasesToText,
  entityTypeLabel,
  fmtDate,
  identifiersToText,
  parseAliasesText,
  parseIdentifiersText,
  parseProfileDataText,
  profileDataToText,
  profileStatusLabel,
  pushRecentEntity,
  verificationLabel,
} from "@/components/dossiers/utils";

type SectionKey = "overview" | "info" | "history" | "relations" | "evidence" | "insights";

const SECTIONS: { key: SectionKey; label: string; icon: typeof UserCircle2; future?: string }[] = [
  { key: "overview", label: "Visão geral", icon: UserCircle2 },
  { key: "info", label: "Informações", icon: FileText },
  { key: "history", label: "Histórico", icon: History, future: "D3 — Relationship History" },
  { key: "relations", label: "Relações", icon: GitBranch, future: "D4 — Connections" },
  { key: "evidence", label: "Pesquisa e evidências", icon: SearchCheck },
  { key: "insights", label: "Insights", icon: Lightbulb, future: "D5 — Strategic Insights" },
];

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Falha ao carregar dados.";
}

export function DossierEntityPage() {
  const { entityId } = useParams();
  const [entity, setEntity] = useState<EntityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [section, setSection] = useState<SectionKey>("overview");

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);

  const [dups, setDups] = useState<DuplicateCandidatesResponse | null>(null);
  const [dupsLoading, setDupsLoading] = useState(false);
  const [dupsError, setDupsError] = useState<string | null>(null);

  const [form, setForm] = useState({
    entity_type: "person",
    canonical_name: "",
    description: "",
    primary_location: "",
    profile_status: "active",
    verification_status: "nao_verificado",
    aliasesText: "",
    identifiersText: "",
    profileDataText: "",
  });

  const load = useCallback(async () => {
    if (!entityId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.getEntity(entityId);
      setEntity(data);
      const summary: EntitySummary = {
        id: data.id,
        entity_type: data.entity_type,
        canonical_name: data.canonical_name,
        normalized_name: data.normalized_name,
        description: data.description,
        profile_status: data.profile_status,
        primary_location: data.primary_location,
        verification_status: data.verification_status,
        confidence: data.confidence,
        source_first_id: data.source_first_id,
        first_seen_at: data.first_seen_at,
        last_seen_at: data.last_seen_at,
        created_at: data.created_at,
        updated_at: data.updated_at,
      };
      pushRecentEntity(summary);
    } catch (err) {
      setError(getErrorMessage(err));
      setEntity(null);
    } finally {
      setLoading(false);
    }
  }, [entityId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!entity) return;
    setForm({
      entity_type: entity.entity_type,
      canonical_name: entity.canonical_name,
      description: entity.description ?? "",
      primary_location: entity.primary_location ?? "",
      profile_status: entity.profile_status ?? "active",
      verification_status: entity.verification_status ?? "nao_verificado",
      aliasesText: aliasesToText(entity.aliases),
      identifiersText: identifiersToText(entity.identifiers),
      profileDataText: profileDataToText(entity.profile_data),
    });
  }, [entity]);

  const activeSection = useMemo(() => SECTIONS.find((s) => s.key === section) ?? SECTIONS[0], [section]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!entityId) return;
    setSaveError(null);
    setJsonError(null);
    const profileData = form.profileDataText.trim() ? parseProfileDataText(form.profileDataText) : null;
    if (form.profileDataText.trim() && profileData === null) {
      setJsonError("profile_data deve ser um objeto JSON válido.");
      return;
    }
    const payload: EntityUpdatePayload = {
      entity_type: form.entity_type,
      canonical_name: form.canonical_name.trim(),
      description: form.description.trim() || null,
      primary_location: form.primary_location.trim() || null,
      profile_status: form.profile_status,
      verification_status: form.verification_status,
      profile_data: profileData,
      aliases: parseAliasesText(form.aliasesText),
      identifiers: parseIdentifiersText(form.identifiersText),
    };
    if (!payload.canonical_name) {
      setSaveError("Nome principal é obrigatório.");
      return;
    }
    setSaving(true);
    try {
      const updated = await api.updateEntity(entityId, payload);
      setEntity(updated);
      setEditing(false);
      setDups(null);
    } catch (err) {
      setSaveError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function loadDuplicates() {
    if (!entityId) return;
    setDupsLoading(true);
    setDupsError(null);
    try {
      const res = await api.listDuplicateCandidates(entityId, 10);
      setDups(res);
    } catch (err) {
      setDupsError(getErrorMessage(err));
      setDups(null);
    } finally {
      setDupsLoading(false);
    }
  }

  if (!entityId) {
    return <PageState kind="error" title="Entidade inválida" description="Identificador de entidade não informado." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
        <Link to="/dossiers" className="inline-flex items-center gap-1 hover:text-foreground"><ArrowLeft className="h-4 w-4" /> Voltar para Dossiers</Link>
      </div>

      {loading && <PageState kind="loading" title="Carregando dossiê" description="Consultando entidade no registro local..." />}
      {error && <PageState kind="error" title="Erro ao carregar dossiê" description={error} />}

      {!loading && !error && entity && (
        <>
          <PageHeader
            title={entity.canonical_name}
            description={entity.description || "Perfil de entidade (D1). Consulte informações cadastrais e navegue pelas seções do dossiê."}
            icon={<UserCircle2 className="h-5 w-5" />}
            badge={entityTypeLabel(entity.entity_type)}
            actions={
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" onClick={() => void load()}><RefreshCw className="h-4 w-4" /> Atualizar</Button>
                <Button variant="outline" size="sm" onClick={() => void loadDuplicates()} disabled={dupsLoading}><SearchCheck className="h-4 w-4" /> {dupsLoading ? "Analisando..." : "Duplicidades"}</Button>
                <Button size="sm" onClick={() => setEditing((v) => !v)}><Pencil className="h-4 w-4" /> {editing ? "Fechar edição" : "Editar"}</Button>
              </div>
            }
          />

          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">{profileStatusLabel(entity.profile_status)}</Badge>
            <Badge variant="outline">{verificationLabel(entity.verification_status)}</Badge>
            <span className="text-xs text-muted-foreground self-center">Atualizado: {fmtDate(entity.updated_at)} · Criado: {fmtDate(entity.created_at)}</span>
          </div>

          {dupsError && <PageState kind="error" title="Erro ao analisar duplicidades" description={dupsError} />}
          {dups && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Possíveis duplicidades (sugestão, sem fusão automática)</CardTitle>
                <CardDescription>Candidatos identificados por correspondência de nome/alternativos/identificadores. A fusão ou descarte requer decisão humana e não é executada automaticamente.</CardDescription>
              </CardHeader>
              <CardContent>
                {dups.items.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhum candidato identificado com os critérios atuais.</p>
                ) : (
                  <div className="space-y-2">
                    {dups.items.map((d) => (
                      <div key={d.candidate.id} className="rounded-md border border-border p-3 text-sm">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <Link to={`/dossiers/${encodeURIComponent(d.candidate.id)}`} className="font-medium text-foreground hover:underline">{d.candidate.canonical_name}</Link>
                          <Badge variant={d.score_level === "high" ? "accent" : "outline"}>{d.score_level === "high" ? "Alta indicação" : d.score_level === "medium" ? "Indicação média" : "Indicação baixa"}</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">{entityTypeLabel(d.candidate.entity_type)} · {profileStatusLabel(d.candidate.profile_status)}</div>
                        <div className="mt-1 text-xs text-muted-foreground">Motivos: {d.reasons.join(", ")}</div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {editing && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-base">Editar entidade</CardTitle><CardDescription>Atualização cadastral com rastreabilidade (auditoria e histórico de alterações).</CardDescription></CardHeader>
              <CardContent>
                <form className="space-y-4" onSubmit={handleSave}>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Tipo</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value })}>
                        {ENTITY_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </label>
                    <label className="block space-y-1 text-sm sm:col-span-2"><span className="text-muted-foreground">Nome principal *</span>
                      <Input value={form.canonical_name} onChange={(e) => setForm({ ...form, canonical_name: e.target.value })} required />
                    </label>
                    <label className="block space-y-1 text-sm sm:col-span-2 lg:col-span-3"><span className="text-muted-foreground">Descrição curta</span>
                      <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                    </label>
                    <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Localização</span>
                      <Input value={form.primary_location} onChange={(e) => setForm({ ...form, primary_location: e.target.value })} />
                    </label>
                    <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Status do perfil</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={form.profile_status} onChange={(e) => setForm({ ...form, profile_status: e.target.value })}>
                        {PROFILE_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </label>
                    <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Verificação</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={form.verification_status} onChange={(e) => setForm({ ...form, verification_status: e.target.value })}>
                        {VERIFICATION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </label>
                    <label className="block space-y-1 text-sm sm:col-span-2 lg:col-span-1"><span className="text-muted-foreground">Nomes alternativos (1 por linha)</span>
                      <textarea className="min-h-[84px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={form.aliasesText} onChange={(e) => setForm({ ...form, aliasesText: e.target.value })} />
                    </label>
                    <label className="block space-y-1 text-sm sm:col-span-2"><span className="text-muted-foreground">Identificadores (tipo:valor, 1 por linha)</span>
                      <textarea className="min-h-[84px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono" value={form.identifiersText} onChange={(e) => setForm({ ...form, identifiersText: e.target.value })} />
                    </label>
                    <label className="block space-y-1 text-sm sm:col-span-2 lg:col-span-3"><span className="text-muted-foreground">Atributos do perfil (JSON)</span>
                      <textarea className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono" value={form.profileDataText} onChange={(e) => setForm({ ...form, profileDataText: e.target.value })} />
                    </label>
                  </div>
                  {jsonError && <div className="text-sm text-destructive">{jsonError}</div>}
                  {saveError && <div className="text-sm text-destructive">{saveError}</div>}
                  <div className="flex flex-wrap gap-2">
                    <Button type="submit" disabled={saving}>{saving ? "Salvando..." : "Salvar alterações"}</Button>
                    <Button type="button" variant="outline" onClick={() => setEditing(false)}>Cancelar</Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          <div className="flex flex-wrap gap-2 border-b border-border pb-2">
            {SECTIONS.map((s) => {
              const Icon = s.icon;
              const active = s.key === section;
              return (
                <button key={s.key} type="button" onClick={() => setSection(s.key)} className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors ${active ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground"}`} aria-current={active ? "page" : undefined}>
                  <Icon className="h-4 w-4" /> {s.label}
                </button>
              );
            })}
          </div>

          {activeSection.key === "evidence" ? (
            <ResearchWorkspace entityId={entity.id} />
          ) : (activeSection.key === "overview" || activeSection.key === "info") ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-base">Visão geral</CardTitle></CardHeader>
                <CardContent className="space-y-2 text-sm text-muted-foreground">
                  <div>Tipo: <span className="text-foreground">{entityTypeLabel(entity.entity_type)}</span></div>
                  <div>Status do perfil: <span className="text-foreground">{profileStatusLabel(entity.profile_status)}</span></div>
                  <div>Verificação: <span className="text-foreground">{verificationLabel(entity.verification_status)}</span></div>
                  <div>Localização: <span className="text-foreground">{entity.primary_location || "—"}</span></div>
                  <div>Origem (source_first_id): <span className="text-foreground break-all">{entity.source_first_id || "—"}</span></div>
                  <div>Primeira visão: <span className="text-foreground">{fmtDate(entity.first_seen_at)}</span></div>
                  <div>Última visão: <span className="text-foreground">{fmtDate(entity.last_seen_at)}</span></div>
                  <div>Atualizado em: <span className="text-foreground">{fmtDate(entity.updated_at)}</span></div>
                  <div>Criado em: <span className="text-foreground">{fmtDate(entity.created_at)}</span></div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-base">Identificadores e nomes alternativos</CardTitle></CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div>
                    <div className="text-muted-foreground mb-1">Identificadores</div>
                    {entity.identifiers.length === 0 ? <div className="text-muted-foreground">—</div> : (
                      <ul className="space-y-1">
                        {entity.identifiers.map((id) => (
                          <li key={id.id} className="text-foreground break-all"><span className="text-muted-foreground">{id.id_type}:</span> {id.value}{id.is_primary ? " (principal)" : ""}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div>
                    <div className="text-muted-foreground mb-1">Nomes alternativos</div>
                    {entity.aliases.length === 0 ? <div className="text-muted-foreground">—</div> : (
                      <ul className="list-disc pl-5 space-y-1 text-foreground">
                        {entity.aliases.map((a) => <li key={a.id}>{a.name}{a.alias_type ? ` (${a.alias_type})` : ""}</li>)}
                      </ul>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card className="lg:col-span-2">
                <CardHeader className="pb-2"><CardTitle className="text-base">Informações do perfil (atributos por tipo)</CardTitle><CardDescription>Dados cadastrais estruturados em profile_data (D1). Fontes, afirmações e evidências por registro são gerenciadas na seção Pesquisa e evidências (D2).</CardDescription></CardHeader>
                <CardContent>
                  {entity.profile_data && Object.keys(entity.profile_data).length > 0 ? (
                    <pre className="text-xs bg-secondary/30 rounded-md p-3 overflow-auto max-h-80 text-foreground">{JSON.stringify(entity.profile_data, null, 2)}</pre>
                  ) : (
                    <p className="text-sm text-muted-foreground">Nenhum atributo estruturado registrado ainda. Use “Editar” para adicionar informações (ex.: ocupação, setor, site, estrutura, observações).</p>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <PageState
              kind="development"
              title={`${activeSection.label} — disponível em subetapa futura${activeSection.future ? ` (${activeSection.future})` : ""}`}
              description="Esta seção faz parte do escopo do Dossiers V1.0, mas ainda não está implementada. Nenhum dado, relação, histórico ou insight é simulado nesta tela. As informações exibidas aqui, quando implementadas, preservarão origem, evidência, temporalidade e distinção entre fato, declaração, inferência e hipótese."
            />
          )}
        </>
      )}
    </div>
  );
}
