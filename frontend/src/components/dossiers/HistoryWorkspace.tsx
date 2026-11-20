import { useCallback, useEffect, useState } from "react";
import { Clock3, Plus, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageState } from "@/components/shared/PageState";
import { api } from "@/lib/api/client";
import type {
  InteractionCreatePayload,
  InteractionDetail,
  InteractionSummary,
  InteractionSummaryResponse,
  InteractionUpdatePayload,
} from "@/lib/api/types";
import {
  INTERACTION_NATURE_OPTIONS,
  INTERACTION_STATUS_OPTIONS,
  INTERACTION_TYPE_OPTIONS,
  TIME_PRECISION_OPTIONS,
  fmtDate,
  interactionNatureLabel,
  interactionStatusLabel,
  interactionTypeLabel,
  timePrecisionLabel,
  verificationLabel,
  VERIFICATION_OPTIONS,
} from "@/components/dossiers/utils";

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Falha ao carregar dados.";
}

function toIsoOrNull(value: string): string | null {
  const v = value.trim();
  if (!v) return null;
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

export function HistoryWorkspace({ entityId }: { entityId: string }) {
  const [summary, setSummary] = useState<InteractionSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [items, setItems] = useState<InteractionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    q: "",
    interaction_type: "",
    nature: "",
    status: "",
    sort: "occurred_desc",
  });

  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formMsg, setFormMsg] = useState<string | null>(null);
  const [form, setForm] = useState({
    interaction_type: "meeting",
    title: "",
    description: "",
    nature: "declarado",
    status: "registered",
    occurred_at: "",
    started_at: "",
    ended_at: "",
    time_precision: "",
    channel: "",
    location_text: "",
    participants_text: "",
    source_locator: "",
    document_id: "",
    research_source_id: "",
    raw_record_id: "",
    claim_id: "",
    evidence_id: "",
    confidence: "",
    justification: "",
    verification_status: "nao_verificado",
  });

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<InteractionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const res = await api.getInteractionsSummary(entityId);
      setSummary(res);
    } catch (err) {
      setSummaryError(getErrorMessage(err));
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, [entityId]);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listEntityInteractions(entityId, {
        q: filters.q.trim() || undefined,
        interaction_type: filters.interaction_type || undefined,
        nature: filters.nature || undefined,
        status: filters.status || undefined,
        sort: filters.sort,
        limit: 100,
        offset: 0,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      setError(getErrorMessage(err));
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [entityId, filters]);

  const loadDetail = useCallback(async (interactionId: string) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const res = await api.getInteraction(interactionId);
      setDetail(res);
    } catch (err) {
      setDetailError(getErrorMessage(err));
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  useEffect(() => {
    if (selectedId) void loadDetail(selectedId);
    else setDetail(null);
  }, [selectedId, loadDetail]);

  const refreshAll = async () => {
    await Promise.all([loadSummary(), loadList()]);
    if (selectedId) await loadDetail(selectedId);
  };

  async function submitCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormMsg(null);
    try {
      const payload: InteractionCreatePayload = {
        interaction_type: form.interaction_type.trim() || "other",
        title: form.title.trim(),
        description: form.description.trim() || null,
        nature: form.nature,
        status: form.status || "registered",
        occurred_at: toIsoOrNull(form.occurred_at),
        started_at: toIsoOrNull(form.started_at),
        ended_at: toIsoOrNull(form.ended_at),
        time_precision: form.time_precision || null,
        channel: form.channel.trim() || null,
        location_text: form.location_text.trim() || null,
        participants_text: form.participants_text.trim() || null,
        source_locator: form.source_locator.trim() || null,
        document_id: form.document_id.trim() || null,
        research_source_id: form.research_source_id.trim() || null,
        raw_record_id: form.raw_record_id.trim() || null,
        claim_id: form.claim_id.trim() || null,
        evidence_id: form.evidence_id.trim() || null,
        confidence: form.confidence ? Number(form.confidence) : null,
        justification: form.justification.trim() || null,
        verification_status: form.verification_status || "nao_verificado",
      };
      if (!payload.title) {
        setFormMsg("Título é obrigatório.");
        return;
      }
      await api.createInteraction(entityId, payload);
      setFormMsg("Interação registrada.");
      setForm({
        interaction_type: "meeting",
        title: "",
        description: "",
        nature: "declarado",
        status: "registered",
        occurred_at: "",
        started_at: "",
        ended_at: "",
        time_precision: "",
        channel: "",
        location_text: "",
        participants_text: "",
        source_locator: "",
        document_id: "",
        research_source_id: "",
        raw_record_id: "",
        claim_id: "",
        evidence_id: "",
        confidence: "",
        justification: "",
        verification_status: "nao_verificado",
      });
      setShowForm(false);
      await Promise.all([loadList(), loadSummary()]);
    } catch (err) {
      setFormMsg(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function quickUpdate(interactionId: string, payload: InteractionUpdatePayload) {
    setUpdatingStatus(true);
    try {
      await api.updateInteraction(interactionId, payload);
      await Promise.all([loadList(), loadSummary()]);
      if (selectedId === interactionId) await loadDetail(interactionId);
    } catch (err) {
      setDetailError(getErrorMessage(err));
    } finally {
      setUpdatingStatus(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2 flex flex-row items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">Histórico de interações (D3 — Relationship History)</CardTitle>
            <CardDescription>
              Linha do tempo rastreável de interações. Cada registro explicita sua natureza (declarado, observado,
              interpretado, a confirmar) e estado; interpretações não são promovidas a fato automaticamente.
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => void refreshAll()}>
            <RefreshCw className="h-4 w-4" /> Atualizar
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {summaryLoading && <PageState kind="loading" title="Carregando resumo" />}
          {summaryError && <PageState kind="error" title="Erro no resumo" description={summaryError} />}
          {summary && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Stat label="Interações" value={summary.interactions_count} />
              <Stat label="Pendentes (a confirmar/revisão)" value={summary.pending_confirmation_or_review} warn={summary.pending_confirmation_or_review > 0} />
              <div className="rounded-md border border-border p-3 text-sm sm:col-span-2">
                <div className="text-xs text-muted-foreground">Período (ocorrência registrada)</div>
                <div className="text-foreground">{summary.earliest_occurred_at ? fmtDate(summary.earliest_occurred_at) : "—"} → {summary.latest_occurred_at ? fmtDate(summary.latest_occurred_at) : "—"}</div>
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  {Object.entries(summary.by_nature).map(([k, v]) => (
                    <Badge key={k} variant="outline">{interactionNatureLabel(k)}: {v}</Badge>
                  ))}
                  {Object.keys(summary.by_nature).length === 0 && <span className="text-muted-foreground">Sem distribuições ainda.</span>}
                </div>
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm text-muted-foreground">Total: {total}</div>
            <Button size="sm" onClick={() => setShowForm((v) => !v)}><Plus className="h-4 w-4" /> Registrar interação</Button>
          </div>

          {showForm && (
            <form onSubmit={submitCreate} className="rounded-md border border-border p-3 space-y-2 text-sm">
              <div className="grid gap-2 sm:grid-cols-2">
                <label className="space-y-1"><span className="text-muted-foreground">Tipo *</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={form.interaction_type} onChange={(e) => setForm({ ...form, interaction_type: e.target.value })}>
                    {INTERACTION_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="space-y-1"><span className="text-muted-foreground">Natureza *</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={form.nature} onChange={(e) => setForm({ ...form, nature: e.target.value })}>
                    {INTERACTION_NATURE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Título *</span>
                  <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
                </label>
                <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Descrição/contexto</span>
                  <textarea className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
                </label>
                <label className="space-y-1"><span className="text-muted-foreground">Status</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                    {INTERACTION_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="space-y-1"><span className="text-muted-foreground">Verificação</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={form.verification_status} onChange={(e) => setForm({ ...form, verification_status: e.target.value })}>
                    {VERIFICATION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="space-y-1"><span className="text-muted-foreground">Ocorrência (data/hora)</span>
                  <Input type="datetime-local" value={form.occurred_at} onChange={(e) => setForm({ ...form, occurred_at: e.target.value })} />
                </label>
                <label className="space-y-1"><span className="text-muted-foreground">Precisão temporal</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={form.time_precision} onChange={(e) => setForm({ ...form, time_precision: e.target.value })}>
                    <option value="">—</option>
                    {TIME_PRECISION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="space-y-1"><span className="text-muted-foreground">Início</span><Input type="datetime-local" value={form.started_at} onChange={(e) => setForm({ ...form, started_at: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">Fim</span><Input type="datetime-local" value={form.ended_at} onChange={(e) => setForm({ ...form, ended_at: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">Canal</span><Input value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">Local</span><Input value={form.location_text} onChange={(e) => setForm({ ...form, location_text: e.target.value })} /></label>
                <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Participantes (descritivo)</span><Input value={form.participants_text} onChange={(e) => setForm({ ...form, participants_text: e.target.value })} /></label>
                <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Localizador/origem (URL/ref.)</span><Input value={form.source_locator} onChange={(e) => setForm({ ...form, source_locator: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">ID documento</span><Input value={form.document_id} onChange={(e) => setForm({ ...form, document_id: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">ID fonte de pesquisa</span><Input value={form.research_source_id} onChange={(e) => setForm({ ...form, research_source_id: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">ID raw_record</span><Input value={form.raw_record_id} onChange={(e) => setForm({ ...form, raw_record_id: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">ID afirmação</span><Input value={form.claim_id} onChange={(e) => setForm({ ...form, claim_id: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">ID evidência</span><Input value={form.evidence_id} onChange={(e) => setForm({ ...form, evidence_id: e.target.value })} /></label>
                <label className="space-y-1"><span className="text-muted-foreground">Confiança (0-1)</span><Input value={form.confidence} onChange={(e) => setForm({ ...form, confidence: e.target.value })} placeholder="ex.: 0.8" /></label>
                <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Justificativa (importante para interpretado/a confirmar)</span><Input value={form.justification} onChange={(e) => setForm({ ...form, justification: e.target.value })} /></label>
              </div>
              {formMsg && <div className="text-xs text-muted-foreground">{formMsg}</div>}
              <div className="flex gap-2">
                <Button type="submit" size="sm" disabled={saving}>{saving ? "Salvando..." : "Salvar interação"}</Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setShowForm(false)}>Cancelar</Button>
              </div>
            </form>
          )}

          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5 text-sm">
            <label className="space-y-1 lg:col-span-2"><span className="text-muted-foreground">Busca</span>
              <Input value={filters.q} onChange={(e) => setFilters({ ...filters, q: e.target.value })} placeholder="título, descrição, canal, participantes..." />
            </label>
            <label className="space-y-1"><span className="text-muted-foreground">Tipo</span>
              <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={filters.interaction_type} onChange={(e) => setFilters({ ...filters, interaction_type: e.target.value })}>
                <option value="">Todos</option>
                {INTERACTION_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </label>
            <label className="space-y-1"><span className="text-muted-foreground">Natureza</span>
              <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={filters.nature} onChange={(e) => setFilters({ ...filters, nature: e.target.value })}>
                <option value="">Todas</option>
                {INTERACTION_NATURE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </label>
            <label className="space-y-1"><span className="text-muted-foreground">Status</span>
              <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
                <option value="">Todos</option>
                {INTERACTION_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </label>
          </div>

          {loading && <PageState kind="loading" title="Carregando interações" description="Consultando linha do tempo..." />}
          {error && <PageState kind="error" title="Erro ao carregar interações" description={error} />}
          {!loading && !error && items.length === 0 && (
            <PageState kind="empty" title="Nenhuma interação registrada" description="Registre interações para construir o histórico rastreável desta entidade (sem inferência automática)." />
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-2">
              {items.map((it) => (
                <button key={it.id} type="button" onClick={() => setSelectedId(it.id)} className={`w-full text-left rounded-md border p-3 text-sm transition-colors ${selectedId === it.id ? "border-primary bg-secondary/30" : "border-border hover:bg-secondary/20"}`}>
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <Clock3 className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{it.title}</span>
                    <Badge variant="outline">{interactionTypeLabel(it.interaction_type)}</Badge>
                    <Badge variant={it.nature === "interpretado" || it.nature === "a_confirmar" ? "accent" : "secondary"}>{interactionNatureLabel(it.nature)}</Badge>
                    <Badge variant="outline">{interactionStatusLabel(it.status)}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Ocorrência: {it.occurred_at ? fmtDate(it.occurred_at) : "—"}{it.time_precision ? ` (${timePrecisionLabel(it.time_precision)})` : ""} · Canal: {it.channel || "—"} · Local: {it.location_text || "—"}
                  </div>
                  {it.description && <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{it.description}</div>}
                </button>
              ))}
            </div>

            <div className="space-y-2">
              {!selectedId && <div className="rounded-md border border-dashed border-border p-4 text-sm text-muted-foreground">Selecione uma interação para ver detalhes e proveniência.</div>}
              {selectedId && detailLoading && <PageState kind="loading" title="Carregando detalhe" />}
              {selectedId && detailError && <PageState kind="error" title="Erro ao carregar detalhe" description={detailError} />}
              {selectedId && detail && !detailLoading && (
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">{detail.title}</CardTitle>
                    <CardDescription className="flex flex-wrap gap-2">
                      <Badge variant="outline">{interactionTypeLabel(detail.interaction_type)}</Badge>
                      <Badge variant={detail.nature === "interpretado" || detail.nature === "a_confirmar" ? "accent" : "secondary"}>{interactionNatureLabel(detail.nature)}</Badge>
                      <Badge variant="outline">{interactionStatusLabel(detail.status)}</Badge>
                      <Badge variant="outline">{verificationLabel(detail.verification_status)}</Badge>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div><span className="text-muted-foreground">Descrição:</span> <span className="text-foreground whitespace-pre-wrap">{detail.description || "—"}</span></div>
                    <div className="grid gap-1 sm:grid-cols-2 text-xs text-muted-foreground">
                      <div>Ocorrência: <span className="text-foreground">{fmtDate(detail.occurred_at)}</span></div>
                      <div>Precisão: <span className="text-foreground">{detail.time_precision ? timePrecisionLabel(detail.time_precision) : "—"}</span></div>
                      <div>Início: <span className="text-foreground">{fmtDate(detail.started_at)}</span></div>
                      <div>Fim: <span className="text-foreground">{fmtDate(detail.ended_at)}</span></div>
                      <div>Canal: <span className="text-foreground">{detail.channel || "—"}</span></div>
                      <div>Local: <span className="text-foreground">{detail.location_text || "—"}</span></div>
                      <div className="sm:col-span-2">Participantes: <span className="text-foreground">{detail.participants_text || "—"}</span></div>
                      <div className="sm:col-span-2 break-all">Localizador: <span className="text-foreground">{detail.source_locator || "—"}</span></div>
                      <div>Documento: <span className="text-foreground break-all">{detail.document_id || "—"}</span></div>
                      <div>Fonte pesquisa: <span className="text-foreground break-all">{detail.research_source_id || "—"}</span></div>
                      <div>Raw record: <span className="text-foreground break-all">{detail.raw_record_id || "—"}</span></div>
                      <div>Afirmação: <span className="text-foreground break-all">{detail.claim_id || "—"}</span></div>
                      <div>Evidência: <span className="text-foreground break-all">{detail.evidence_id || "—"}</span></div>
                      <div>Confiança: <span className="text-foreground">{detail.confidence ?? "—"}</span></div>
                      <div>Atualizado: <span className="text-foreground">{fmtDate(detail.updated_at)}</span></div>
                      <div className="sm:col-span-2">Justificativa: <span className="text-foreground whitespace-pre-wrap">{detail.justification || "—"}</span></div>
                    </div>
                    <div className="flex flex-wrap gap-2 pt-1">
                      <Button size="sm" variant="outline" disabled={updatingStatus} onClick={() => void quickUpdate(detail.id, { status: "confirmed" })}>Marcar confirmada</Button>
                      <Button size="sm" variant="outline" disabled={updatingStatus} onClick={() => void quickUpdate(detail.id, { status: "needs_review" })}>Requer revisão</Button>
                      <Button size="sm" variant="outline" disabled={updatingStatus} onClick={() => void quickUpdate(detail.id, { status: "cancelled" })}>Cancelar registro</Button>
                    </div>
                    <div className="text-xs text-muted-foreground">Ações de estado são explícitas e rastreáveis; não há promoção automática a fato.</div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value, warn }: { label: string; value: number; warn?: boolean }) {
  return (
    <div className={`rounded-md border p-3 ${warn ? "border-destructive/40 bg-destructive/5" : "border-border"}`}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-xl font-semibold text-foreground">{value}</div>
    </div>
  );
}
