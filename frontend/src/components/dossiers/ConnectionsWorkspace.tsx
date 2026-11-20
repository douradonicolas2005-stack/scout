import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import cytoscape, { type Core, type ElementDefinition } from "cytoscape";
import { AlertCircle, Link2, Network, Plus, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api/client";
import type {
  ConnectionCreatePayload,
  ConnectionDetail,
  ConnectionSummary,
  ConnectionSummaryResponse,
  ConnectionUpdatePayload,
  EntitySummary,
  TaxonomyRelationType,
} from "@/lib/api/types";
import {
  CONNECTION_DIRECTION_OPTIONS,
  CONNECTION_NATURE_OPTIONS,
  CONNECTION_STATUS_OPTIONS,
  CONNECTION_TIME_PRECISION_OPTIONS,
  CONNECTION_VERIFICATION_OPTIONS,
  connectionNatureLabel,
  connectionStatusLabel,
  connectionTimePrecisionLabel,
  connectionVerificationLabel,
  entityTypeLabel,
  fmtDate,
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

function confidenceOrNull(value: string): number | null {
  const v = value.trim();
  if (!v) return null;
  const n = Number(v);
  if (Number.isNaN(n)) return null;
  return n;
}

interface Props {
  entityId: string;
  entityType: string;
}

export function ConnectionsWorkspace({ entityId, entityType }: Props) {
  const [items, setItems] = useState<ConnectionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<ConnectionSummaryResponse | null>(null);
  const [taxonomy, setTaxonomy] = useState<TaxonomyRelationType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState("");
  const [filterDirection, setFilterDirection] = useState("");
  const [filterRelationType, setFilterRelationType] = useState("");
  const [filterCategory, setFilterCategory] = useState("");
  const [filterNature, setFilterNature] = useState("");
  const [filterVerification, setFilterVerification] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [hasEvidence, setHasEvidence] = useState<"" | "true" | "false">("");

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<ConnectionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formMsg, setFormMsg] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  // form fields
  const [otherQuery, setOtherQuery] = useState("");
  const [otherResults, setOtherResults] = useState<EntitySummary[]>([]);
  const [selectedOther, setSelectedOther] = useState<EntitySummary | null>(null);
  const [relationType, setRelationType] = useState("");
  const [anchorRole, setAnchorRole] = useState<"from" | "to">("from");
  const [nature, setNature] = useState("declarado");
  const [verificationStatus, setVerificationStatus] = useState("nao_verificado");
  const [status, setStatus] = useState("active");
  const [occurredAt, setOccurredAt] = useState("");
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");
  const [timePrecision, setTimePrecision] = useState("");
  const [confidence, setConfidence] = useState("");
  const [description, setDescription] = useState("");
  const [justification, setJustification] = useState("");
  const [sourceLocator, setSourceLocator] = useState("");
  const [createdBy, setCreatedBy] = useState("human_user:local");

  const graphContainerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const [showGraph, setShowGraph] = useState(true);
  const [graphError, setGraphError] = useState<string | null>(null);

  const approvedTypes = useMemo(() => taxonomy.filter((t) => t.status_mvp === "approved"), [taxonomy]);
  const selectedSpec = useMemo(() => taxonomy.find((t) => t.id === relationType) ?? null, [taxonomy, relationType]);
  const categories = useMemo(() => Array.from(new Set(taxonomy.map((t) => t.category))).sort(), [taxonomy]);

  const compatibleOther = useCallback(
    (spec: TaxonomyRelationType | null, candidateType: string) => {
      if (!spec) return true;
      if (spec.directionality === "undirected") {
        const anchorOkFrom = spec.from_entity_types.includes(entityType);
        const anchorOkTo = spec.to_entity_types.includes(entityType);
        const candOkFrom = spec.from_entity_types.includes(candidateType);
        const candOkTo = spec.to_entity_types.includes(candidateType);
        return (anchorOkFrom && candOkTo) || (anchorOkTo && candOkFrom);
      }
      if (anchorRole === "from") return spec.to_entity_types.includes(candidateType);
      return spec.from_entity_types.includes(candidateType);
    },
    [entityType, anchorRole],
  );

  const loadTaxonomy = useCallback(async () => {
    try {
      const res = await api.getConnectionsTaxonomy();
      setTaxonomy(res.items);
    } catch {
      // non-fatal
    }
  }, []);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [listRes, sumRes] = await Promise.all([
        api.listEntityConnections(entityId, {
          q: q || undefined,
          direction: filterDirection || undefined,
          relation_type: filterRelationType || undefined,
          category: filterCategory || undefined,
          nature: filterNature || undefined,
          verification_status: filterVerification || undefined,
          status: filterStatus || undefined,
          has_evidence: hasEvidence === "" ? undefined : hasEvidence === "true",
          sort: "updated_desc",
          limit: 50,
          offset: 0,
        }),
        api.getConnectionsSummary(entityId),
      ]);
      setItems(listRes.items);
      setTotal(listRes.total);
      setSummary(sumRes);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [entityId, q, filterDirection, filterRelationType, filterCategory, filterNature, filterVerification, filterStatus, hasEvidence]);

  const loadDetail = useCallback(async (id: string) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const res = await api.getConnection(id, entityId);
      setSelected(res);
    } catch (err) {
      setDetailError(getErrorMessage(err));
      setSelected(null);
    } finally {
      setDetailLoading(false);
    }
  }, [entityId]);

  useEffect(() => { void loadTaxonomy(); }, [loadTaxonomy]);
  useEffect(() => { void loadList(); }, [loadList]);
  useEffect(() => {
    if (selectedId) void loadDetail(selectedId);
    else setSelected(null);
  }, [selectedId, loadDetail]);

  useEffect(() => {
    const t = setTimeout(async () => {
      const term = otherQuery.trim();
      if (!term || selectedOther) { setOtherResults([]); return; }
      try {
        const res = await api.listEntities({ q: term, limit: 8 });
        setOtherResults(res.items.filter((e) => e.id !== entityId && compatibleOther(selectedSpec, e.entity_type)));
      } catch { setOtherResults([]); }
    }, 250);
    return () => clearTimeout(t);
  }, [otherQuery, selectedOther, entityId, selectedSpec, compatibleOther]);

  useEffect(() => {
    if (selectedOther && !compatibleOther(selectedSpec, selectedOther.entity_type)) {
      setSelectedOther(null);
      setOtherQuery("");
    }
  }, [relationType, anchorRole, selectedSpec, selectedOther, compatibleOther]);

  async function submitCreate(e: React.FormEvent) {
    e.preventDefault();
    setFormMsg(null);
    if (!selectedOther) { setFormMsg("Selecione a entidade relacionada (busca)."); return; }
    if (!relationType) { setFormMsg("Selecione o tipo de relação aprovado."); return; }
    if (!createdBy.trim()) { setFormMsg("created_by é obrigatório (formato: human_user:<id>)."); return; }
    const spec = selectedSpec;
    if (!spec) { setFormMsg("Tipo de relação inválido."); return; }
    const payload: ConnectionCreatePayload = {
      relation_type: relationType,
      other_entity_id: selectedOther.id,
      nature: nature as ConnectionCreatePayload["nature"],
      verification_status: verificationStatus as ConnectionCreatePayload["verification_status"],
      status: status as ConnectionCreatePayload["status"],
      description: description.trim() || null,
      justification: justification.trim() || null,
      source_locator: sourceLocator.trim() || null,
      occurred_at: toIsoOrNull(occurredAt),
      valid_from: toIsoOrNull(validFrom),
      valid_to: toIsoOrNull(validTo),
      time_precision: (timePrecision || null) as ConnectionCreatePayload["time_precision"],
      confidence: confidenceOrNull(confidence),
      created_by: createdBy.trim(),
    };
    if (spec.directionality === "directed") payload.anchor_role = anchorRole;
    setSaving(true);
    try {
      await api.createConnection(entityId, payload);
      setFormMsg("Conexão registrada com rastreabilidade.");
      setShowForm(false);
      setSelectedOther(null); setOtherQuery(""); setRelationType("");
      setDescription(""); setJustification(""); setSourceLocator("");
      setConfidence(""); setOccurredAt(""); setValidFrom(""); setValidTo("");
      await loadList();
    } catch (err) {
      setFormMsg(getErrorMessage(err));
    } finally { setSaving(false); }
  }

  async function quickUpdate(connectionId: string, payload: ConnectionUpdatePayload) {
    setUpdating(true);
    try {
      await api.updateConnection(connectionId, payload, entityId);
      await loadList();
      if (selectedId === connectionId) await loadDetail(connectionId);
    } catch (err) {
      setDetailError(getErrorMessage(err));
    } finally { setUpdating(false); }
  }

  const graphElements = useMemo<ElementDefinition[]>(() => {
    const nodes = new Map<string, ElementDefinition>();
    nodes.set(entityId, { data: { id: entityId, label: "Entidade atual", kind: "center" } });
    const edges: ElementDefinition[] = [];
    for (const it of items) {
      const other = it.counterpart_entity;
      const otherId = other?.id || (it.from_entity_id === entityId ? it.to_entity_id : it.from_entity_id);
      if (!nodes.has(otherId)) {
        nodes.set(otherId, { data: { id: otherId, label: other ? other.canonical_name : otherId.slice(0, 8), kind: "other" } });
      }
      edges.push({
        data: {
          id: it.id,
          source: it.from_entity_id,
          target: it.to_entity_id,
          label: it.perspective_label || it.relation_type_name || it.relation_type,
          directed: it.directionality === "directed" ? 1 : 0,
        },
      });
    }
    return [...nodes.values(), ...edges];
  }, [items, entityId]);

  useEffect(() => {
    if (!showGraph || graphError) {
      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }
      return;
    }
    if (!graphContainerRef.current || items.length === 0) return;
    try {
      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }
      const cy = cytoscape({
        container: graphContainerRef.current,
        elements: graphElements,
        style: [
          { selector: "node", style: { label: "data(label)", "font-size": 10, "text-valign": "center", "text-halign": "center", "background-color": "#94a3b8", color: "#0f172a", width: 28, height: 28, "text-wrap": "wrap", "text-max-width": 90 } as any },
          { selector: 'node[kind = "center"]', style: { "background-color": "#2563eb", width: 34, height: 34, "font-weight": 700 } as any },
          { selector: "edge", style: { label: "data(label)", "font-size": 8, "curve-style": "bezier", "target-arrow-shape": "none", "line-color": "#64748b", "target-arrow-color": "#64748b", width: 2, "text-rotation": "autorotate", "text-background-opacity": 1, "text-background-color": "#ffffff", "text-background-padding": 2 } as any },
          { selector: "edge[directed = 1]", style: { "target-arrow-shape": "triangle" } as any },
        ],
        layout: { name: "cose", animate: false, fit: true, padding: 20 } as any,
      });
      cy.on("tap", "node", (evt) => {
        const id = evt.target.id();
        if (id && id !== entityId) window.location.hash = `#/dossiers/${id}`;
      });
      cyRef.current = cy;
      setGraphError(null);
    } catch (e) {
      setGraphError(getErrorMessage(e));
    }
    return () => {
      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }
    };
  }, [graphElements, showGraph, items.length, entityId, graphError]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2 flex flex-row items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base flex items-center gap-2"><Link2 className="h-4 w-4" /> Conexões (D4 — Connections)</CardTitle>
            <CardDescription>
              Relações reais cadastradas entre entidades. Natureza, verificação e estado são separados; inferências não são promovidas a fato automaticamente. Lista estruturada é a visualização principal.
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => void loadList()} disabled={loading}><RefreshCw className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`} />Atualizar</Button>
            <Button size="sm" onClick={() => setShowForm((v) => !v)}><Plus className="h-4 w-4 mr-1" />Nova conexão</Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {summary ? (
            <div className="flex flex-wrap gap-2 text-xs">
              <Badge variant="outline">Total: {summary.connections_count}</Badge>
              <Badge variant="secondary">Saída: {summary.outgoing_count}</Badge>
              <Badge variant="secondary">Entrada: {summary.incoming_count}</Badge>
              <Badge variant="secondary">Simétricas: {summary.undirected_count}</Badge>
              <Badge variant="outline">Com lastro: {summary.with_evidence_count}</Badge>
              {Object.entries(summary.by_status).map(([k, v]) => (<Badge key={k} variant="outline">{connectionStatusLabel(k)}: {v}</Badge>))}
            </div>
          ) : null}

          <div className="grid gap-2 md:grid-cols-4">
            <Input placeholder="Buscar (tipo, descrição, justificativa, locator)" value={q} onChange={(e) => setQ(e.target.value)} />
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={filterDirection} onChange={(e) => setFilterDirection(e.target.value)}>
              {CONNECTION_DIRECTION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
              <option value="">Todas categorias</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={filterRelationType} onChange={(e) => setFilterRelationType(e.target.value)}>
              <option value="">Todos tipos</option>
              {taxonomy.map((t) => <option key={t.id} value={t.id}>{t.id} ({t.status_mvp})</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={filterNature} onChange={(e) => setFilterNature(e.target.value)}>
              <option value="">Todas naturezas</option>
              {CONNECTION_NATURE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={filterVerification} onChange={(e) => setFilterVerification(e.target.value)}>
              <option value="">Toda verificação</option>
              {CONNECTION_VERIFICATION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
              <option value="">Todos estados</option>
              {CONNECTION_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={hasEvidence} onChange={(e) => setHasEvidence(e.target.value as "" | "true" | "false")}>
              <option value="">Lastro: todos</option>
              <option value="true">Com lastro</option>
              <option value="false">Sem lastro</option>
            </select>
          </div>

          {error ? (
            <div className="flex items-center gap-2 text-sm text-destructive"><AlertCircle className="h-4 w-4" />{error}<Button size="sm" variant="outline" onClick={() => void loadList()}>Tentar novamente</Button></div>
          ) : null}
        </CardContent>
      </Card>

      {showForm ? (
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Registrar conexão (explícita)</CardTitle><CardDescription>Use apenas tipos aprovados da taxonomia. Sem inferência automática. `created_by` obrigatório (formato controlado).</CardDescription></CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={submitCreate}>
              <div className="grid gap-3 md:grid-cols-2">
                <label className="block space-y-1 text-sm md:col-span-2"><span className="text-muted-foreground">Tipo de relação (aprovado) *</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={relationType} onChange={(e) => setRelationType(e.target.value)}>
                    <option value="">Selecione...</option>
                    {approvedTypes.map((t) => <option key={t.id} value={t.id}>[{t.category}] {t.name} ({t.id}) — {t.directionality}</option>)}
                  </select>
                  {selectedSpec ? <p className="text-xs text-muted-foreground">{selectedSpec.description} {selectedSpec.notes ? `(${selectedSpec.notes})` : ""}</p> : null}
                </label>

                {selectedSpec?.directionality === "directed" ? (
                  <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Papel da entidade atual</span>
                    <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={anchorRole} onChange={(e) => setAnchorRole(e.target.value as "from" | "to")}>
                      <option value="from">Origem (from) — relação parte desta entidade</option>
                      <option value="to">Destino (to) — relação aponta para esta entidade</option>
                    </select>
                  </label>
                ) : null}

                <label className="block space-y-1 text-sm md:col-span-2"><span className="text-muted-foreground">Entidade relacionada (busca, tipos compatíveis) *</span>
                  {selectedOther ? (
                    <div className="flex items-center gap-2 text-sm"><Badge variant="secondary">{selectedOther.canonical_name}</Badge><span className="text-muted-foreground">{entityTypeLabel(selectedOther.entity_type)}</span><Button type="button" size="sm" variant="ghost" onClick={() => { setSelectedOther(null); setOtherQuery(""); }}>Trocar</Button></div>
                  ) : (
                    <div className="space-y-1">
                      <Input value={otherQuery} onChange={(e) => setOtherQuery(e.target.value)} placeholder="Buscar por nome..." />
                      {otherResults.length > 0 ? (
                        <div className="rounded-md border p-1 space-y-1 max-h-40 overflow-auto">
                          {otherResults.map((r) => (
                            <button type="button" key={r.id} className="w-full text-left px-2 py-1 text-sm hover:bg-muted rounded" onClick={() => { setSelectedOther(r); setOtherQuery(r.canonical_name); setOtherResults([]); }}>
                              {r.canonical_name} <span className="text-muted-foreground">({entityTypeLabel(r.entity_type)})</span>
                            </button>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  )}
                </label>

                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Natureza</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={nature} onChange={(e) => setNature(e.target.value)}>
                    {CONNECTION_NATURE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Verificação</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={verificationStatus} onChange={(e) => setVerificationStatus(e.target.value)}>
                    {CONNECTION_VERIFICATION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Estado</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}>
                    {CONNECTION_STATUS_OPTIONS.filter((o) => o.value !== "archived").map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Confiança (0-1, opcional)</span>
                  <Input type="number" step="0.01" min="0" max="1" value={confidence} onChange={(e) => setConfidence(e.target.value)} />
                </label>
                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Ocorrido em</span><Input type="datetime-local" value={occurredAt} onChange={(e) => setOccurredAt(e.target.value)} /></label>
                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Precisão temporal</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={timePrecision} onChange={(e) => setTimePrecision(e.target.value)}>
                    {CONNECTION_TIME_PRECISION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </label>
                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Válido de</span><Input type="datetime-local" value={validFrom} onChange={(e) => setValidFrom(e.target.value)} /></label>
                <label className="block space-y-1 text-sm"><span className="text-muted-foreground">Válido até</span><Input type="datetime-local" value={validTo} onChange={(e) => setValidTo(e.target.value)} /></label>
                <label className="block space-y-1 text-sm md:col-span-2"><span className="text-muted-foreground">Descrição</span><Input value={description} onChange={(e) => setDescription(e.target.value)} /></label>
                <label className="block space-y-1 text-sm md:col-span-2"><span className="text-muted-foreground">Justificativa (fundamentação/lastro)</span><Input value={justification} onChange={(e) => setJustification(e.target.value)} /></label>
                <label className="block space-y-1 text-sm md:col-span-2"><span className="text-muted-foreground">Localizador de fonte (complementar)</span><Input value={sourceLocator} onChange={(e) => setSourceLocator(e.target.value)} placeholder="URL, referência, citação curta..." /></label>
                <label className="block space-y-1 text-sm md:col-span-2"><span className="text-muted-foreground">created_by (obrigatório) *</span><Input value={createdBy} onChange={(e) => setCreatedBy(e.target.value)} placeholder="human_user:local" /></label>
              </div>
              {formMsg ? <p className={`text-sm ${formMsg.includes("Falha") || formMsg.includes("obrig") || formMsg.includes("Selecione") || formMsg.includes("invál") ? "text-destructive" : "text-emerald-700"}`}>{formMsg}</p> : null}
              <div className="flex gap-2"><Button type="submit" disabled={saving}>{saving ? "Salvando..." : "Salvar conexão"}</Button><Button type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancelar</Button></div>
            </form>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Lista de conexões</CardTitle><CardDescription>{total} registro(s) encontrado(s).</CardDescription></CardHeader>
          <CardContent>
            {loading ? <p className="text-sm text-muted-foreground">Carregando conexões...</p> : items.length === 0 ? (
              <p className="text-sm text-muted-foreground">Nenhuma conexão registrada para os filtros atuais.</p>
            ) : (
              <div className="space-y-2 max-h-[520px] overflow-auto pr-1">
                {items.map((it) => (
                  <button key={it.id} type="button" onClick={() => setSelectedId(it.id)} className={`w-full text-left rounded-md border p-3 hover:bg-muted/40 ${selectedId === it.id ? "border-primary" : ""}`}>
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <Badge variant="secondary">{it.relation_type_name || it.relation_type}</Badge>
                      <Badge variant={it.directionality === "directed" ? "outline" : "default"}>{it.directionality === "directed" ? "dirigida" : "simétrica"}</Badge>
                      <Badge variant="outline">{connectionNatureLabel(it.nature || "")}</Badge>
                      <Badge variant="outline">{connectionVerificationLabel(it.verification_status || "")}</Badge>
                      <Badge variant={it.status === "archived" ? "accent" : "outline"}>{connectionStatusLabel(it.status || "")}</Badge>
                      {it.has_evidence ? <Badge variant="default">lastro</Badge> : null}
                    </div>
                    <div className="text-sm font-medium">
                      {it.perspective_label || it.relation_type_name || it.relation_type}
                      {" — "}
                      {it.counterpart_entity ? <Link to={`/dossiers/${it.counterpart_entity.id}`} className="underline" onClick={(e) => e.stopPropagation()}>{it.counterpart_entity.canonical_name}</Link> : "—"}
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      Vigência: {fmtDate(it.valid_from)} → {fmtDate(it.valid_to)} · Precisão: {connectionTimePrecisionLabel(it.time_precision || "")} · Atualizado: {fmtDate(it.updated_at)}
                    </div>
                    {it.nature === "inferido" ? <p className="text-xs text-amber-700 mt-1">Relação inferida — não é fato verificado.</p> : null}
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Detalhe da conexão</CardTitle><CardDescription>Metadados, proveniência, temporalidade e ações explícitas.</CardDescription></CardHeader>
          <CardContent>
            {!selectedId ? <p className="text-sm text-muted-foreground">Selecione uma conexão na lista.</p> : detailLoading ? <p className="text-sm text-muted-foreground">Carregando detalhe...</p> : detailError ? <div className="text-sm text-destructive">{detailError}</div> : selected ? (
              <div className="space-y-3 text-sm">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">{selected.relation_type_name || selected.relation_type}</Badge>
                  <Badge variant="outline">{selected.directionality}</Badge>
                  <Badge variant="outline">Natureza: {connectionNatureLabel(selected.nature || "")}</Badge>
                  <Badge variant="outline">Verificação: {connectionVerificationLabel(selected.verification_status || "")}</Badge>
                  <Badge variant={selected.status === "archived" ? "accent" : "outline"}>Estado: {connectionStatusLabel(selected.status || "")}</Badge>
                </div>
                <div className="grid gap-2 md:grid-cols-2">
                  <div><span className="text-muted-foreground">De:</span> <Link className="underline" to={`/dossiers/${selected.from_entity_id}`}>{selected.from_entity?.canonical_name || selected.from_entity_id}</Link></div>
                  <div><span className="text-muted-foreground">Para:</span> <Link className="underline" to={`/dossiers/${selected.to_entity_id}`}>{selected.to_entity?.canonical_name || selected.to_entity_id}</Link></div>
                  <div><span className="text-muted-foreground">Perspectiva (âncora):</span> {selected.perspective_label || "—"}</div>
                  <div><span className="text-muted-foreground">Tipo inverso equivalente:</span> {selected.inverse_type_id || "—"}</div>
                  <div><span className="text-muted-foreground">Ocorrido em:</span> {fmtDate(selected.occurred_at)}</div>
                  <div><span className="text-muted-foreground">Precisão temporal:</span> {connectionTimePrecisionLabel(selected.time_precision || "")}</div>
                  <div><span className="text-muted-foreground">Válido de:</span> {fmtDate(selected.valid_from)}</div>
                  <div><span className="text-muted-foreground">Válido até:</span> {fmtDate(selected.valid_to)}</div>
                  <div><span className="text-muted-foreground">Confiança:</span> {selected.confidence ?? "—"}</div>
                  <div><span className="text-muted-foreground">created_by:</span> {selected.created_by || "— (legado/compatibilidade)"}</div>
                  <div><span className="text-muted-foreground">claim_id:</span> {selected.claim_id || "—"}</div>
                  <div><span className="text-muted-foreground">evidence_id:</span> {selected.evidence_id || "—"}</div>
                </div>
                {selected.source_locator ? <div><span className="text-muted-foreground">Localizador:</span> {selected.source_locator}</div> : null}
                {selected.description ? <div><span className="text-muted-foreground">Descrição:</span> {selected.description}</div> : null}
                {selected.justification ? <div><span className="text-muted-foreground">Justificativa:</span> {selected.justification}</div> : null}
                <div className="text-xs text-muted-foreground">Criado: {fmtDate(selected.created_at)} · Atualizado: {fmtDate(selected.updated_at)}</div>
                {selected.nature === "inferido" ? <div className="text-amber-700 text-xs">Relação inferida: não é fato verificado e não pode ser promovida a verificada sem reclassificação explícita de natureza.</div> : null}

                <div className="border-t pt-3 space-y-2">
                  <div className="font-medium text-sm">Ações explícitas</div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" variant="outline" disabled={updating || selected.status === "archived"} onClick={() => void quickUpdate(selected.id, { status: "needs_review" })}>Marcar revisão</Button>
                    <Button size="sm" variant="outline" disabled={updating || selected.status === "archived"} onClick={() => void quickUpdate(selected.id, { status: "inactive" })}>Inativar</Button>
                    <Button size="sm" variant="outline" disabled={updating || selected.status === "archived"} onClick={() => void quickUpdate(selected.id, { verification_status: "contestado" })}>Contestar</Button>
                    <Button size="sm" variant="outline" disabled={updating || selected.status === "archived" || selected.nature === "inferido"} onClick={() => void quickUpdate(selected.id, { verification_status: "verificado" })}>Marcar verificado</Button>
                    <Button size="sm" variant="destructive" disabled={updating || selected.status === "archived"} onClick={() => void quickUpdate(selected.id, { status: "archived" })}>Arquivar</Button>
                  </div>
                  {selected.status === "archived" ? <p className="text-xs text-muted-foreground">Registros arquivados não podem ser reativados diretamente; crie um novo registro para vínculo restabelecido.</p> : null}
                  {selected.nature === "inferido" ? <p className="text-xs text-muted-foreground">Verificação direta bloqueada para natureza inferida (reclassifique a natureza explicitamente antes).</p> : null}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2 flex flex-row items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base flex items-center gap-2"><Network className="h-4 w-4" />Grafo ego-network (1 salto, complementar)</CardTitle>
            <CardDescription>Somente relações reais cadastradas. Dirigidas com seta; simétricas sem seta. Fallback: use a lista acima se o grafo falhar.</CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => setShowGraph((v) => !v)}>{showGraph ? "Ocultar grafo" : "Mostrar grafo"}</Button>
        </CardHeader>
        <CardContent>
          {graphError ? (
            <div className="text-sm text-destructive flex items-center gap-2"><AlertCircle className="h-4 w-4" />Falha ao renderizar grafo (fallback: lista estruturada). {graphError}<Button size="sm" variant="outline" onClick={() => { setGraphError(null); setShowGraph(true); }}>Tentar novamente</Button></div>
          ) : showGraph ? (
            items.length === 0 ? <p className="text-sm text-muted-foreground">Sem relações para exibir no grafo.</p> : (
              <div ref={graphContainerRef} className="h-[320px] rounded-md border overflow-hidden" />
            )
          ) : <p className="text-sm text-muted-foreground">Grafo oculto. A lista estruturada permanece disponível.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
