import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, FileText, Link2, Plus, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageState } from "@/components/shared/PageState";
import { api } from "@/lib/api/client";
import type {
  ClaimConflictCreatePayload,
  ClaimCreatePayload,
  ClaimSummary,
  DocumentCreatePayload,
  DocumentSummary,
  EvidenceCreatePayload,
  ResearchSourceCreatePayload,
  ResearchSourceSummary,
  ResearchSummaryResponse,
} from "@/lib/api/types";
import { fmtDate, verificationLabel, VERIFICATION_OPTIONS } from "@/components/dossiers/utils";
import {
  CLAIM_TYPE_OPTIONS,
  CONFLICT_STATUS_OPTIONS,
  EVIDENCE_RELATION_OPTIONS,
  RELIABILITY_OPTIONS,
  labelFor,
  shortId,
} from "@/components/dossiers/researchUtils";

type TabKey = "summary" | "documents" | "sources" | "claims" | "conflicts";

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Falha ao carregar dados.";
}

export function ResearchWorkspace({ entityId }: { entityId: string }) {
  const [tab, setTab] = useState<TabKey>("summary");
  const [summary, setSummary] = useState<ResearchSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [docsTotal, setDocsTotal] = useState(0);
  const [docsLoading, setDocsLoading] = useState(false);
  const [docsError, setDocsError] = useState<string | null>(null);

  const [sources, setSources] = useState<ResearchSourceSummary[]>([]);
  const [sourcesTotal, setSourcesTotal] = useState(0);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [sourcesError, setSourcesError] = useState<string | null>(null);

  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [claimsTotal, setClaimsTotal] = useState(0);
  const [claimsLoading, setClaimsLoading] = useState(false);
  const [claimsError, setClaimsError] = useState<string | null>(null);

  const [conflicts, setConflicts] = useState<Array<{ id: string; claim_id: string; conflicting_claim_id: string; conflict_type: string; status: string; description: string | null }>>([]);
  const [conflictsTotal, setConflictsTotal] = useState(0);
  const [conflictsLoading, setConflictsLoading] = useState(false);
  const [conflictsError, setConflictsError] = useState<string | null>(null);

  // forms
  const [showDocForm, setShowDocForm] = useState(false);
  const [docForm, setDocForm] = useState({ title: "", document_type: "", source_locator: "", research_source_id: "", description: "", verification_status: "nao_verificado", origin_type: "manual", is_reference_only: true });
  const [docSaving, setDocSaving] = useState(false);
  const [docMsg, setDocMsg] = useState<string | null>(null);

  const [showSourceForm, setShowSourceForm] = useState(false);
  const [sourceForm, setSourceForm] = useState({ name: "", source_type: "site", url: "", domain: "", description: "", reliability_status: "nao_avaliada", verification_status: "nao_verificado", reliability_justification: "" });
  const [sourceSaving, setSourceSaving] = useState(false);
  const [sourceMsg, setSourceMsg] = useState<string | null>(null);

  const [showClaimForm, setShowClaimForm] = useState(false);
  const [claimForm, setClaimForm] = useState({ claim_text: "", claim_type: "declaracao", verification_status: "nao_verificado", confidence: "", justification: "", research_source_id: "", document_id: "", occurred_at: "" });
  const [claimSaving, setClaimSaving] = useState(false);
  const [claimMsg, setClaimMsg] = useState<string | null>(null);

  const [expandedClaim, setExpandedClaim] = useState<string | null>(null);
  const [evForm, setEvForm] = useState({ relation_type: "supports", evidence_type: "", snippet: "", excerpt: "", locator: "", note: "", research_source_id: "", document_id: "" });
  const [evSaving, setEvSaving] = useState(false);
  const [evMsg, setEvMsg] = useState<string | null>(null);

  const [confForm, setConfForm] = useState({ claim_id: "", conflicting_claim_id: "", conflict_type: "contradicao", description: "", status: "open" });
  const [confSaving, setConfSaving] = useState(false);
  const [confMsg, setConfMsg] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    setSummaryLoading(true);
    setSummaryError(null);
    try {
      const res = await api.getResearchSummary(entityId);
      setSummary(res);
    } catch (err) {
      setSummaryError(getErrorMessage(err));
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, [entityId]);

  const loadDocs = useCallback(async () => {
    setDocsLoading(true);
    setDocsError(null);
    try {
      const res = await api.listEntityDocuments(entityId, { limit: 50, offset: 0, sort: "updated_desc" });
      setDocs(res.items);
      setDocsTotal(res.total);
    } catch (err) {
      setDocsError(getErrorMessage(err));
    } finally {
      setDocsLoading(false);
    }
  }, [entityId]);

  const loadSources = useCallback(async () => {
    setSourcesLoading(true);
    setSourcesError(null);
    try {
      const res = await api.listResearchSources({ limit: 100, offset: 0, sort: "updated_desc" });
      setSources(res.items);
      setSourcesTotal(res.total);
    } catch (err) {
      setSourcesError(getErrorMessage(err));
    } finally {
      setSourcesLoading(false);
    }
  }, []);

  const loadClaims = useCallback(async () => {
    setClaimsLoading(true);
    setClaimsError(null);
    try {
      const res = await api.listEntityClaims(entityId, { limit: 50, offset: 0, sort: "updated_desc" });
      setClaims(res.items);
      setClaimsTotal(res.total);
    } catch (err) {
      setClaimsError(getErrorMessage(err));
    } finally {
      setClaimsLoading(false);
    }
  }, [entityId]);

  const loadConflicts = useCallback(async () => {
    setConflictsLoading(true);
    setConflictsError(null);
    try {
      const res = await api.listEntityConflicts(entityId, { limit: 100, offset: 0 });
      setConflicts(res.items);
      setConflictsTotal(res.total);
    } catch (err) {
      setConflictsError(getErrorMessage(err));
    } finally {
      setConflictsLoading(false);
    }
  }, [entityId]);

  useEffect(() => { void loadSummary(); }, [loadSummary]);
  useEffect(() => {
    if (tab === "documents") void loadDocs();
    if (tab === "sources") void loadSources();
    if (tab === "claims") void loadClaims();
    if (tab === "conflicts") void loadConflicts();
  }, [tab, loadDocs, loadSources, loadClaims, loadConflicts]);

  const refreshAll = async () => {
    await loadSummary();
    if (tab === "documents") await loadDocs();
    if (tab === "sources") await loadSources();
    if (tab === "claims") await loadClaims();
    if (tab === "conflicts") await loadConflicts();
  };

  async function submitDoc(e: React.FormEvent) {
    e.preventDefault();
    setDocSaving(true); setDocMsg(null);
    try {
      const payload: DocumentCreatePayload = {
        title: docForm.title.trim() || null,
        document_type: docForm.document_type.trim() || null,
        source_locator: docForm.source_locator.trim() || null,
        research_source_id: docForm.research_source_id.trim() || null,
        description: docForm.description.trim() || null,
        verification_status: docForm.verification_status,
        origin_type: docForm.origin_type,
        is_reference_only: docForm.is_reference_only,
        entity_ids: [entityId],
      };
      if (!payload.source_locator && !payload.research_source_id) {
        setDocMsg("Informe ao menos um localizador/origem (source_locator) ou uma fonte de pesquisa.");
        return;
      }
      await api.createDocument(entityId, payload);
      setDocMsg("Documento registrado.");
      setDocForm({ title: "", document_type: "", source_locator: "", research_source_id: "", description: "", verification_status: "nao_verificado", origin_type: "manual", is_reference_only: true });
      setShowDocForm(false);
      await Promise.all([loadDocs(), loadSummary()]);
    } catch (err) {
      setDocMsg(getErrorMessage(err));
    } finally {
      setDocSaving(false);
    }
  }

  async function submitSource(e: React.FormEvent) {
    e.preventDefault();
    setSourceSaving(true); setSourceMsg(null);
    try {
      const payload: ResearchSourceCreatePayload = {
        name: sourceForm.name.trim(),
        source_type: sourceForm.source_type.trim() || "outro",
        url: sourceForm.url.trim() || null,
        domain: sourceForm.domain.trim() || null,
        description: sourceForm.description.trim() || null,
        reliability_status: sourceForm.reliability_status,
        verification_status: sourceForm.verification_status,
        reliability_justification: sourceForm.reliability_justification.trim() || null,
      };
      if (!payload.name) { setSourceMsg("Nome é obrigatório."); return; }
      await api.createResearchSource(payload);
      setSourceMsg("Fonte de pesquisa registrada.");
      setSourceForm({ name: "", source_type: "site", url: "", domain: "", description: "", reliability_status: "nao_avaliada", verification_status: "nao_verificado", reliability_justification: "" });
      setShowSourceForm(false);
      await Promise.all([loadSources(), loadSummary()]);
    } catch (err) {
      setSourceMsg(getErrorMessage(err));
    } finally {
      setSourceSaving(false);
    }
  }

  async function submitClaim(e: React.FormEvent) {
    e.preventDefault();
    setClaimSaving(true); setClaimMsg(null);
    try {
      const payload: ClaimCreatePayload = {
        claim_text: claimForm.claim_text.trim(),
        claim_type: claimForm.claim_type,
        verification_status: claimForm.verification_status,
        confidence: claimForm.confidence ? Number(claimForm.confidence) : null,
        justification: claimForm.justification.trim() || null,
        research_source_id: claimForm.research_source_id.trim() || null,
        document_id: claimForm.document_id.trim() || null,
        occurred_at: claimForm.occurred_at ? new Date(claimForm.occurred_at).toISOString() : null,
        entity_ids: [entityId],
      };
      if (!payload.claim_text) { setClaimMsg("Texto da afirmação é obrigatório."); return; }
      await api.createClaim(entityId, payload);
      setClaimMsg("Afirmação registrada.");
      setClaimForm({ claim_text: "", claim_type: "declaracao", verification_status: "nao_verificado", confidence: "", justification: "", research_source_id: "", document_id: "", occurred_at: "" });
      setShowClaimForm(false);
      await Promise.all([loadClaims(), loadSummary()]);
    } catch (err) {
      setClaimMsg(getErrorMessage(err));
    } finally {
      setClaimSaving(false);
    }
  }

  async function submitEvidence(claimId: string, e: React.FormEvent) {
    e.preventDefault();
    setEvSaving(true); setEvMsg(null);
    try {
      const payload: EvidenceCreatePayload = {
        relation_type: evForm.relation_type,
        evidence_type: evForm.evidence_type.trim() || null,
        snippet: evForm.snippet.trim() || null,
        excerpt: evForm.excerpt.trim() || null,
        locator: evForm.locator.trim() || null,
        note: evForm.note.trim() || null,
        research_source_id: evForm.research_source_id.trim() || null,
        document_id: evForm.document_id.trim() || null,
      };
      await api.createEvidence(claimId, payload);
      setEvMsg("Evidência registrada.");
      setEvForm({ relation_type: "supports", evidence_type: "", snippet: "", excerpt: "", locator: "", note: "", research_source_id: "", document_id: "" });
      await loadSummary();
    } catch (err) {
      setEvMsg(getErrorMessage(err));
    } finally {
      setEvSaving(false);
    }
  }

  async function submitConflict(e: React.FormEvent) {
    e.preventDefault();
    setConfSaving(true); setConfMsg(null);
    try {
      const payload: ClaimConflictCreatePayload = {
        conflicting_claim_id: confForm.conflicting_claim_id.trim(),
        conflict_type: confForm.conflict_type.trim() || "contradicao",
        description: confForm.description.trim() || null,
        status: confForm.status,
      };
      if (!confForm.claim_id.trim() || !payload.conflicting_claim_id) {
        setConfMsg("Informe os IDs das duas afirmações em conflito.");
        return;
      }
      await api.createClaimConflict(confForm.claim_id.trim(), payload);
      setConfMsg("Conflito registrado.");
      setConfForm({ claim_id: "", conflicting_claim_id: "", conflict_type: "contradicao", description: "", status: "open" });
      await Promise.all([loadConflicts(), loadClaims(), loadSummary()]);
    } catch (err) {
      setConfMsg(getErrorMessage(err));
    } finally {
      setConfSaving(false);
    }
  }

  const tabs: { key: TabKey; label: string }[] = [
    { key: "summary", label: "Resumo" },
    { key: "documents", label: "Documentos" },
    { key: "sources", label: "Fontes de pesquisa" },
    { key: "claims", label: "Afirmações & evidências" },
    { key: "conflicts", label: "Conflitos" },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2 flex flex-row items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">Research Workspace (D2 — Pesquisa & Evidências)</CardTitle>
            <CardDescription>Registro determinístico e rastreável de fontes, documentos, afirmações e evidências. Informações registradas não são automaticamente verdadeiras; inferências não são promovidas a fato sem ação explícita e revisão humana.</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => void refreshAll()}><RefreshCw className="h-4 w-4" /> Atualizar</Button>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 border-b border-border pb-2 mb-4">
            {tabs.map((t) => (
              <button key={t.key} type="button" onClick={() => setTab(t.key)} className={`rounded-md px-3 py-1.5 text-sm ${tab === t.key ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-secondary/50"}`}>{t.label}</button>
            ))}
          </div>

          {tab === "summary" && (
            <div className="space-y-3">
              {summaryLoading && <PageState kind="loading" title="Carregando resumo" description="Consultando indicadores do workspace..." />}
              {summaryError && <PageState kind="error" title="Erro no resumo" description={summaryError} />}
              {summary && (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Stat label="Documentos" value={summary.documents_count} />
                  <Stat label="Fontes de pesquisa referenciadas" value={summary.research_sources_count} />
                  <Stat label="Afirmações" value={summary.claims_count} />
                  <Stat label="Evidências" value={summary.evidence_count} />
                  <Stat label="Afirmações pendentes de verificação" value={summary.pending_verification_claims} />
                  <Stat label="Conflitos abertos/em análise" value={summary.open_conflicts} warn={summary.open_conflicts > 0} />
                  <div className="rounded-md border border-border p-3 text-sm sm:col-span-2 lg:col-span-3">
                    <div className="font-medium mb-1">Afirmações por tipo</div>
                    <div className="flex flex-wrap gap-2">{Object.keys(summary.claims_by_type).length ? Object.entries(summary.claims_by_type).map(([k,v]) => <Badge key={k} variant="outline">{labelFor(CLAIM_TYPE_OPTIONS, k)}: {v}</Badge>) : <span className="text-muted-foreground">Nenhuma afirmação registrada.</span>}</div>
                    <div className="font-medium mt-3 mb-1">Afirmações por verificação</div>
                    <div className="flex flex-wrap gap-2">{Object.keys(summary.claims_by_verification).length ? Object.entries(summary.claims_by_verification).map(([k,v]) => <Badge key={k} variant="secondary">{verificationLabel(k)}: {v}</Badge>) : <span className="text-muted-foreground">—</span>}</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === "documents" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between"><div className="text-sm text-muted-foreground">Total: {docsTotal}</div><Button size="sm" onClick={() => setShowDocForm((v)=>!v)}><Plus className="h-4 w-4" /> Registrar documento</Button></div>
              {showDocForm && (
                <form onSubmit={submitDoc} className="rounded-md border border-border p-3 space-y-2 text-sm">
                  <div className="grid gap-2 sm:grid-cols-2">
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Título</span><Input value={docForm.title} onChange={(e)=>setDocForm({...docForm,title:e.target.value})} /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">Tipo</span><Input value={docForm.document_type} onChange={(e)=>setDocForm({...docForm,document_type:e.target.value})} placeholder="relatorio, contrato, noticia..." /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">Origem</span><Input value={docForm.origin_type} onChange={(e)=>setDocForm({...docForm,origin_type:e.target.value})} /></label>
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Localizador/origem (URL, caminho, referência) *</span><Input value={docForm.source_locator} onChange={(e)=>setDocForm({...docForm,source_locator:e.target.value})} /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">ID da fonte de pesquisa (opcional)</span><Input value={docForm.research_source_id} onChange={(e)=>setDocForm({...docForm,research_source_id:e.target.value})} /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">Verificação</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={docForm.verification_status} onChange={(e)=>setDocForm({...docForm,verification_status:e.target.value})}>{VERIFICATION_OPTIONS.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>
                    </label>
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Descrição</span><Input value={docForm.description} onChange={(e)=>setDocForm({...docForm,description:e.target.value})} /></label>
                    <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={docForm.is_reference_only} onChange={(e)=>setDocForm({...docForm,is_reference_only:e.target.checked})} /> Apenas referência (sem cópia local gerenciada)</label>
                  </div>
                  {docMsg && <div className="text-xs text-muted-foreground">{docMsg}</div>}
                  <Button type="submit" size="sm" disabled={docSaving}>{docSaving?"Salvando...":"Salvar documento"}</Button>
                </form>
              )}
              {docsLoading && <PageState kind="loading" title="Carregando documentos" />}
              {docsError && <PageState kind="error" title="Erro ao carregar documentos" description={docsError} />}
              {!docsLoading && !docsError && docs.length === 0 && <PageState kind="empty" title="Nenhum documento registrado" description="Registre documentos e referências associados a esta entidade." />}
              <div className="space-y-2">{docs.map((d) => (
                <div key={d.id} className="rounded-md border border-border p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2"><FileText className="h-4 w-4 text-muted-foreground" /><span className="font-medium">{d.title || "(sem título)"}</span><Badge variant="outline">{d.document_type || "documento"}</Badge><Badge variant="secondary">{verificationLabel(d.verification_status)}</Badge></div>
                  <div className="text-xs text-muted-foreground mt-1">ID: {shortId(d.id)} · Origem: {d.origin_type || "—"} · Fonte pesquisa: {shortId(d.research_source_id)} · Atualizado: {fmtDate(d.updated_at)}</div>
                  {d.source_locator && <div className="text-xs mt-1 break-all"><span className="text-muted-foreground">Localizador:</span> {d.source_locator}</div>}
                  {d.is_reference_only && <div className="text-xs text-muted-foreground">Apenas referência (sem cópia local gerenciada).</div>}
                </div>
              ))}</div>
            </div>
          )}

          {tab === "sources" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between"><div className="text-sm text-muted-foreground">Total no catálogo local: {sourcesTotal} (listagem global de fontes de pesquisa)</div><Button size="sm" onClick={() => setShowSourceForm((v)=>!v)}><Plus className="h-4 w-4" /> Nova fonte</Button></div>
              {showSourceForm && (
                <form onSubmit={submitSource} className="rounded-md border border-border p-3 space-y-2 text-sm">
                  <div className="grid gap-2 sm:grid-cols-2">
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Nome *</span><Input value={sourceForm.name} onChange={(e)=>setSourceForm({...sourceForm,name:e.target.value})} required /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">Tipo</span><Input value={sourceForm.source_type} onChange={(e)=>setSourceForm({...sourceForm,source_type:e.target.value})} /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">Domínio</span><Input value={sourceForm.domain} onChange={(e)=>setSourceForm({...sourceForm,domain:e.target.value})} /></label>
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">URL</span><Input value={sourceForm.url} onChange={(e)=>setSourceForm({...sourceForm,url:e.target.value})} /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">Confiabilidade</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={sourceForm.reliability_status} onChange={(e)=>setSourceForm({...sourceForm,reliability_status:e.target.value})}>{RELIABILITY_OPTIONS.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>
                    </label>
                    <label className="space-y-1"><span className="text-muted-foreground">Verificação</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={sourceForm.verification_status} onChange={(e)=>setSourceForm({...sourceForm,verification_status:e.target.value})}>{VERIFICATION_OPTIONS.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>
                    </label>
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Justificativa da confiabilidade</span><Input value={sourceForm.reliability_justification} onChange={(e)=>setSourceForm({...sourceForm,reliability_justification:e.target.value})} /></label>
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Descrição</span><Input value={sourceForm.description} onChange={(e)=>setSourceForm({...sourceForm,description:e.target.value})} /></label>
                  </div>
                  {sourceMsg && <div className="text-xs text-muted-foreground">{sourceMsg}</div>}
                  <Button type="submit" size="sm" disabled={sourceSaving}>{sourceSaving?"Salvando...":"Salvar fonte"}</Button>
                </form>
              )}
              {sourcesLoading && <PageState kind="loading" title="Carregando fontes" />}
              {sourcesError && <PageState kind="error" title="Erro ao carregar fontes" description={sourcesError} />}
              {!sourcesLoading && !sourcesError && sources.length === 0 && <PageState kind="empty" title="Nenhuma fonte de pesquisa registrada" description="Cadastre fontes consultadas para rastreabilidade das afirmações e documentos." />}
              <div className="space-y-2">{sources.map((s) => (
                <div key={s.id} className="rounded-md border border-border p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2"><Link2 className="h-4 w-4 text-muted-foreground" /><span className="font-medium">{s.name}</span><Badge variant="outline">{s.source_type}</Badge><Badge variant="secondary">{labelFor(RELIABILITY_OPTIONS, s.reliability_status)}</Badge><Badge variant="outline">{verificationLabel(s.verification_status)}</Badge></div>
                  <div className="text-xs text-muted-foreground mt-1">ID: {shortId(s.id)} · Domínio: {s.domain || "—"} · Atualizado: {fmtDate(s.updated_at)}</div>
                  {s.url && <div className="text-xs mt-1 break-all">{s.url}</div>}
                </div>
              ))}</div>
            </div>
          )}

          {tab === "claims" && (
            <div className="space-y-3">
              <div className="flex items-center justify-between"><div className="text-sm text-muted-foreground">Total: {claimsTotal} · Afirmações registradas (não são fatos automaticamente).</div><Button size="sm" onClick={() => setShowClaimForm((v)=>!v)}><Plus className="h-4 w-4" /> Registrar afirmação</Button></div>
              {showClaimForm && (
                <form onSubmit={submitClaim} className="rounded-md border border-border p-3 space-y-2 text-sm">
                  <div className="grid gap-2 sm:grid-cols-2">
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Texto da afirmação *</span>
                      <textarea className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={claimForm.claim_text} onChange={(e)=>setClaimForm({...claimForm,claim_text:e.target.value})} required />
                    </label>
                    <label className="space-y-1"><span className="text-muted-foreground">Tipo (epistemológico)</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={claimForm.claim_type} onChange={(e)=>setClaimForm({...claimForm,claim_type:e.target.value})}>{CLAIM_TYPE_OPTIONS.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>
                    </label>
                    <label className="space-y-1"><span className="text-muted-foreground">Verificação</span>
                      <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={claimForm.verification_status} onChange={(e)=>setClaimForm({...claimForm,verification_status:e.target.value})}>{VERIFICATION_OPTIONS.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>
                    </label>
                    <label className="space-y-1"><span className="text-muted-foreground">Confiança (0-1)</span><Input value={claimForm.confidence} onChange={(e)=>setClaimForm({...claimForm,confidence:e.target.value})} placeholder="ex.: 0.7" /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">Data de ocorrência (opcional)</span><Input type="date" value={claimForm.occurred_at} onChange={(e)=>setClaimForm({...claimForm,occurred_at:e.target.value})} /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">ID documento origem (opcional)</span><Input value={claimForm.document_id} onChange={(e)=>setClaimForm({...claimForm,document_id:e.target.value})} /></label>
                    <label className="space-y-1"><span className="text-muted-foreground">ID fonte de pesquisa (opcional)</span><Input value={claimForm.research_source_id} onChange={(e)=>setClaimForm({...claimForm,research_source_id:e.target.value})} /></label>
                    <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Justificativa (obrigatória para inferência/hipótese/previsão marcada como verificada)</span><Input value={claimForm.justification} onChange={(e)=>setClaimForm({...claimForm,justification:e.target.value})} /></label>
                  </div>
                  {claimMsg && <div className="text-xs text-muted-foreground">{claimMsg}</div>}
                  <Button type="submit" size="sm" disabled={claimSaving}>{claimSaving?"Salvando...":"Salvar afirmação"}</Button>
                </form>
              )}
              {claimsLoading && <PageState kind="loading" title="Carregando afirmações" />}
              {claimsError && <PageState kind="error" title="Erro ao carregar afirmações" description={claimsError} />}
              {!claimsLoading && !claimsError && claims.length === 0 && <PageState kind="empty" title="Nenhuma afirmação registrada" description="Registre afirmações com classificação epistemológica, origem e justificativa." />}
              <div className="space-y-2">{claims.map((c) => (
                <div key={c.id} className="rounded-md border border-border p-3 text-sm space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{labelFor(CLAIM_TYPE_OPTIONS, c.claim_type)}</Badge>
                    <Badge variant="secondary">{verificationLabel(c.verification_status)}</Badge>
                    {c.conflict_status && c.conflict_status !== "none" && <Badge variant="accent"><AlertTriangle className="h-3 w-3 mr-1 inline" />Conflito: {c.conflict_status}</Badge>}
                  </div>
                  <div className="text-foreground">{c.claim_text}</div>
                  <div className="text-xs text-muted-foreground">ID: {c.id} · Origem: {c.claim_origin} · Doc: {shortId(c.document_id)} · Fonte: {shortId(c.research_source_id)} · Ocorrência: {fmtDate(c.occurred_at)} · Registrada: {fmtDate(c.registered_at || c.created_at)}</div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" onClick={() => setExpandedClaim(expandedClaim === c.id ? null : c.id)}>{expandedClaim === c.id ? "Fechar" : "Adicionar evidência"}</Button>
                    <Button variant="outline" size="sm" onClick={() => { setConfForm({ ...confForm, claim_id: c.id }); setTab("conflicts"); }}>Registrar conflito</Button>
                  </div>
                  {expandedClaim === c.id && (
                    <form onSubmit={(e)=>void submitEvidence(c.id, e)} className="rounded-md border border-dashed border-border p-3 space-y-2">
                      <div className="text-sm font-medium">Nova evidência (vínculo explícito à afirmação)</div>
                      <div className="grid gap-2 sm:grid-cols-2">
                        <label className="space-y-1"><span className="text-muted-foreground text-sm">Relação</span>
                          <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={evForm.relation_type} onChange={(e)=>setEvForm({...evForm,relation_type:e.target.value})}>{EVIDENCE_RELATION_OPTIONS.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>
                        </label>
                        <label className="space-y-1"><span className="text-muted-foreground text-sm">Tipo</span><Input value={evForm.evidence_type} onChange={(e)=>setEvForm({...evForm,evidence_type:e.target.value})} placeholder="trecho, citação, registro..." /></label>
                        <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground text-sm">Trecho/excerto</span><Input value={evForm.excerpt} onChange={(e)=>setEvForm({...evForm,excerpt:e.target.value})} /></label>
                        <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground text-sm">Snippet/contexto</span><Input value={evForm.snippet} onChange={(e)=>setEvForm({...evForm,snippet:e.target.value})} /></label>
                        <label className="space-y-1"><span className="text-muted-foreground text-sm">Localizador (página, seção, URL, âncora)</span><Input value={evForm.locator} onChange={(e)=>setEvForm({...evForm,locator:e.target.value})} /></label>
                        <label className="space-y-1"><span className="text-muted-foreground text-sm">ID documento</span><Input value={evForm.document_id} onChange={(e)=>setEvForm({...evForm,document_id:e.target.value})} /></label>
                        <label className="space-y-1"><span className="text-muted-foreground text-sm">ID fonte de pesquisa</span><Input value={evForm.research_source_id} onChange={(e)=>setEvForm({...evForm,research_source_id:e.target.value})} /></label>
                        <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground text-sm">Nota</span><Input value={evForm.note} onChange={(e)=>setEvForm({...evForm,note:e.target.value})} /></label>
                      </div>
                      {evMsg && <div className="text-xs text-muted-foreground">{evMsg}</div>}
                      <Button type="submit" size="sm" disabled={evSaving}>{evSaving?"Salvando...":"Salvar evidência"}</Button>
                    </form>
                  )}
                </div>
              ))}</div>
            </div>
          )}

          {tab === "conflicts" && (
            <div className="space-y-3">
              <div className="text-sm text-muted-foreground">Total: {conflictsTotal} · Conflitos entre afirmações (identificação e registro explícitos, sem resolução automática).</div>
              <form onSubmit={submitConflict} className="rounded-md border border-border p-3 space-y-2 text-sm">
                <div className="font-medium">Registrar conflito entre afirmações</div>
                <div className="grid gap-2 sm:grid-cols-2">
                  <label className="space-y-1"><span className="text-muted-foreground">ID afirmação A *</span><Input value={confForm.claim_id} onChange={(e)=>setConfForm({...confForm,claim_id:e.target.value})} required /></label>
                  <label className="space-y-1"><span className="text-muted-foreground">ID afirmação B (conflitante) *</span><Input value={confForm.conflicting_claim_id} onChange={(e)=>setConfForm({...confForm,conflicting_claim_id:e.target.value})} required /></label>
                  <label className="space-y-1"><span className="text-muted-foreground">Tipo</span><Input value={confForm.conflict_type} onChange={(e)=>setConfForm({...confForm,conflict_type:e.target.value})} /></label>
                  <label className="space-y-1"><span className="text-muted-foreground">Status</span>
                    <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={confForm.status} onChange={(e)=>setConfForm({...confForm,status:e.target.value})}>{CONFLICT_STATUS_OPTIONS.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>
                  </label>
                  <label className="space-y-1 sm:col-span-2"><span className="text-muted-foreground">Descrição</span><Input value={confForm.description} onChange={(e)=>setConfForm({...confForm,description:e.target.value})} /></label>
                </div>
                {confMsg && <div className="text-xs text-muted-foreground">{confMsg}</div>}
                <Button type="submit" size="sm" disabled={confSaving}>{confSaving?"Salvando...":"Registrar conflito"}</Button>
              </form>
              {conflictsLoading && <PageState kind="loading" title="Carregando conflitos" />}
              {conflictsError && <PageState kind="error" title="Erro ao carregar conflitos" description={conflictsError} />}
              {!conflictsLoading && !conflictsError && conflicts.length === 0 && <PageState kind="empty" title="Nenhum conflito registrado" description="Conflitos aparecem aqui quando duas afirmações são marcadas como contraditórias." />}
              <div className="space-y-2">{conflicts.map((cf) => (
                <div key={cf.id} className="rounded-md border border-border p-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2"><AlertTriangle className="h-4 w-4 text-muted-foreground" /><span className="font-medium">{cf.conflict_type}</span><Badge variant={cf.status === "open" ? "accent" : "secondary"}>{labelFor(CONFLICT_STATUS_OPTIONS, cf.status)}</Badge></div>
                  <div className="text-xs text-muted-foreground mt-1">ID: {shortId(cf.id)} · A: {shortId(cf.claim_id)} · B: {shortId(cf.conflicting_claim_id)}</div>
                  {cf.description && <div className="text-xs mt-1">{cf.description}</div>}
                </div>
              ))}</div>
            </div>
          )}
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
