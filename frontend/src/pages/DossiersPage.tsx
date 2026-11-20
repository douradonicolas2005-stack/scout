import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FolderSearch, Plus, RefreshCw, Search } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PageState } from "@/components/shared/PageState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api/client";
import type { EntityCreatePayload, EntitySummary } from "@/lib/api/types";
import {
  ENTITY_TYPE_OPTIONS,
  PROFILE_STATUS_OPTIONS,
  VERIFICATION_OPTIONS,
  entityTypeLabel,
  fmtDate,
  parseAliasesText,
  parseIdentifiersText,
  parseProfileDataText,
  profileStatusLabel,
  readRecentEntities,
  verificationLabel,
} from "@/components/dossiers/utils";

function getErrorMessage(err: unknown): string {
  return err instanceof Error ? err.message : "Falha ao carregar dados.";
}

interface FormState {
  entity_type: string;
  canonical_name: string;
  description: string;
  primary_location: string;
  profile_status: string;
  verification_status: string;
  aliasesText: string;
  identifiersText: string;
  profileDataText: string;
}

const emptyForm: FormState = {
  entity_type: "person",
  canonical_name: "",
  description: "",
  primary_location: "",
  profile_status: "active",
  verification_status: "nao_verificado",
  aliasesText: "",
  identifiersText: "",
  profileDataText: "",
};

export function DossiersPage() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [entityType, setEntityType] = useState("");
  const [profileStatus, setProfileStatus] = useState("");
  const [verificationStatus, setVerificationStatus] = useState("");
  const [sort, setSort] = useState("updated_desc");

  const [items, setItems] = useState<EntitySummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentUpdated, setRecentUpdated] = useState<EntitySummary[]>([]);
  const [recentCreated, setRecentCreated] = useState<EntitySummary[]>([]);
  const [recentConsulted, setRecentConsulted] = useState<EntitySummary[]>([]);

  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [formJsonError, setFormJsonError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [listRes, updatedRes, createdRes] = await Promise.all([
        api.listEntities({
          q: q || undefined,
          entity_type: entityType || undefined,
          profile_status: profileStatus || undefined,
          verification_status: verificationStatus || undefined,
          sort,
          limit: 30,
          offset: 0,
        }),
        api.listEntities({ sort: "updated_desc", limit: 5, offset: 0 }),
        api.listEntities({ sort: "created_desc", limit: 5, offset: 0 }),
      ]);
      setItems(listRes.items);
      setTotal(listRes.total);
      setRecentUpdated(updatedRes.items);
      setRecentCreated(createdRes.items);
      setRecentConsulted(readRecentEntities());
    } catch (err) {
      setError(getErrorMessage(err));
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [q, entityType, profileStatus, verificationStatus, sort]);

  useEffect(() => {
    void load();
  }, [load]);

  const hasFilters = useMemo(
    () => !!(q || entityType || profileStatus || verificationStatus),
    [q, entityType, profileStatus, verificationStatus],
  );

  function openEntity(id: string) {
    navigate(`/dossiers/${encodeURIComponent(id)}`);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreateError(null);
    setFormJsonError(null);
    const profileData = form.profileDataText.trim() ? parseProfileDataText(form.profileDataText) : null;
    if (form.profileDataText.trim() && profileData === null) {
      setFormJsonError('profile_data deve ser um objeto JSON válido (ex.: {"campo": "valor"}).');
      return;
    }
    const payload: EntityCreatePayload = {
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
      setCreateError("Nome principal é obrigatório.");
      return;
    }
    setCreating(true);
    try {
      const created = await api.createEntity(payload);
      setShowCreate(false);
      setForm(emptyForm);
      await load();
      navigate(`/dossiers/${encodeURIComponent(created.id)}`);
    } catch (err) {
      setCreateError(getErrorMessage(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Dossiers"
        description="Base de conhecimento local de entidades (pessoas, empresas, grupos, instituições e outras). Pesquisa, consulta e cadastro persistente com rastreabilidade — sem simulação de dados ou funcionalidades."
        icon={<FolderSearch className="h-5 w-5" />}
        badge="D1 — Entity Profiles"
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => void load()}>
              <RefreshCw className="h-4 w-4" /> Atualizar
            </Button>
            <Button size="sm" onClick={() => setShowCreate((v) => !v)}>
              <Plus className="h-4 w-4" /> Nova entidade
            </Button>
          </div>
        }
      />

      {showCreate && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Cadastrar entidade</CardTitle>
            <CardDescription>
              Registro cadastral persistente (D1). Informações, evidências, histórico, relações e insights avançados serão incorporados nas subetapas D2–D5.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleCreate}>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <label className="block space-y-1 text-sm">
                  <span className="text-muted-foreground">Tipo *</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={form.entity_type} onChange={(e) => setForm({ ...form, entity_type: e.target.value })}>
                    {ENTITY_TYPE_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </label>
                <label className="block space-y-1 text-sm sm:col-span-2">
                  <span className="text-muted-foreground">Nome principal *</span>
                  <Input value={form.canonical_name} onChange={(e) => setForm({ ...form, canonical_name: e.target.value })} placeholder="Nome canônico da entidade" required />
                </label>
                <label className="block space-y-1 text-sm sm:col-span-2 lg:col-span-3">
                  <span className="text-muted-foreground">Descrição curta</span>
                  <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Resumo breve para o cabeçalho do dossiê" />
                </label>
                <label className="block space-y-1 text-sm">
                  <span className="text-muted-foreground">Localização (nível apropriado)</span>
                  <Input value={form.primary_location} onChange={(e) => setForm({ ...form, primary_location: e.target.value })} placeholder="Cidade, UF / país / região" />
                </label>
                <label className="block space-y-1 text-sm">
                  <span className="text-muted-foreground">Status do perfil</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={form.profile_status} onChange={(e) => setForm({ ...form, profile_status: e.target.value })}>
                    {PROFILE_STATUS_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </label>
                <label className="block space-y-1 text-sm">
                  <span className="text-muted-foreground">Verificação</span>
                  <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={form.verification_status} onChange={(e) => setForm({ ...form, verification_status: e.target.value })}>
                    {VERIFICATION_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </label>
                <label className="block space-y-1 text-sm sm:col-span-2 lg:col-span-1">
                  <span className="text-muted-foreground">Nomes alternativos (1 por linha)</span>
                  <textarea className="min-h-[84px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={form.aliasesText} onChange={(e) => setForm({ ...form, aliasesText: e.target.value })} placeholder="Nome fantasia / alternativo" />
                </label>
                <label className="block space-y-1 text-sm sm:col-span-2">
                  <span className="text-muted-foreground">Identificadores (1 por linha, formato tipo:valor)</span>
                  <textarea className="min-h-[84px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono" value={form.identifiersText} onChange={(e) => setForm({ ...form, identifiersText: e.target.value })} placeholder={"cnpj:00.000.000/0001-00\ndomain:exemplo.com\nexternal_id:..."} />
                </label>
                <label className="block space-y-1 text-sm sm:col-span-2 lg:col-span-3">
                  <span className="text-muted-foreground">Atributos do perfil (JSON opcional, por tipo)</span>
                  <textarea className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono" value={form.profileDataText} onChange={(e) => setForm({ ...form, profileDataText: e.target.value })} placeholder='{"occupation":"...","sector":"...","website":"...","notes":"..."}' />
                </label>
              </div>
              {formJsonError && <div className="text-sm text-destructive">{formJsonError}</div>}
              {createError && <div className="text-sm text-destructive">{createError}</div>}
              <div className="flex flex-wrap gap-2">
                <Button type="submit" disabled={creating}>{creating ? "Salvando..." : "Salvar entidade"}</Button>
                <Button type="button" variant="outline" onClick={() => { setShowCreate(false); setCreateError(null); setFormJsonError(null); }}>Cancelar</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardDescription className="flex items-center gap-2"><Search className="h-4 w-4" /> Pesquisa e consulta local</CardDescription>
          <CardTitle className="text-base">Entidades</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
            <Input placeholder="Buscar por nome, alternativo ou identificador" value={q} onChange={(e) => setQ(e.target.value)} className="sm:col-span-2" aria-label="Buscar entidades" />
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={entityType} onChange={(e) => setEntityType(e.target.value)} aria-label="Filtrar por tipo">
              <option value="">Todos os tipos</option>
              {ENTITY_TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={profileStatus} onChange={(e) => setProfileStatus(e.target.value)} aria-label="Filtrar por status do perfil">
              <option value="">Todos os status</option>
              {PROFILE_STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm" value={verificationStatus} onChange={(e) => setVerificationStatus(e.target.value)} aria-label="Filtrar por verificação">
              <option value="">Todas verificações</option>
              {VERIFICATION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <label className="flex items-center gap-2">Ordenar
              <select className="flex h-8 rounded-md border border-input bg-background px-2 text-sm" value={sort} onChange={(e) => setSort(e.target.value)}>
                <option value="updated_desc">Atualizadas (recentes)</option>
                <option value="created_desc">Criadas (recentes)</option>
                <option value="name_asc">Nome (A–Z)</option>
                <option value="updated_asc">Atualizadas (antigas)</option>
              </select>
            </label>
            <span>{total} resultado(s){hasFilters ? " (filtrado)" : ""}</span>
          </div>

          {loading && <PageState kind="loading" title="Carregando entidades" description="Consultando o registro local de dossiês..." />}
          {error && <PageState kind="error" title="Erro ao carregar entidades" description={error} />}
          {!loading && !error && items.length === 0 && (
            <PageState kind="empty" title={hasFilters ? "Nenhuma entidade encontrada" : "Nenhuma entidade cadastrada"} description={hasFilters ? "Ajuste os filtros ou a busca." : "Cadastre a primeira entidade para iniciar a base de dossiês (D1)."} />
          )}
          {!loading && !error && items.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Entidades cadastradas</caption>
                <thead className="text-xs uppercase text-muted-foreground">
                  <tr className="border-b border-border">
                    <th className="py-2 pr-3 font-medium">Nome</th>
                    <th className="py-2 pr-3 font-medium">Tipo</th>
                    <th className="py-2 pr-3 font-medium">Perfil</th>
                    <th className="py-2 pr-3 font-medium">Verificação</th>
                    <th className="py-2 pr-3 font-medium">Atualização</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((e) => (
                    <tr key={e.id} className="border-b border-border/60 last:border-0 hover:bg-secondary/30 cursor-pointer" onClick={() => openEntity(e.id)}>
                      <td className="py-2 pr-3">
                        <div className="font-medium text-foreground">{e.canonical_name}</div>
                        {e.description ? <div className="text-xs text-muted-foreground line-clamp-1">{e.description}</div> : null}
                      </td>
                      <td className="py-2 pr-3 text-muted-foreground">{entityTypeLabel(e.entity_type)}</td>
                      <td className="py-2 pr-3"><Badge variant={e.profile_status === "active" ? "secondary" : "outline"}>{profileStatusLabel(e.profile_status)}</Badge></td>
                      <td className="py-2 pr-3 text-muted-foreground text-xs">{verificationLabel(e.verification_status)}</td>
                      <td className="py-2 pr-3 text-muted-foreground whitespace-nowrap text-xs">{fmtDate(e.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Recentemente atualizadas</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {recentUpdated.length === 0 ? <p className="text-sm text-muted-foreground">Sem dados ainda.</p> : recentUpdated.map((e) => (
              <button key={e.id} type="button" className="w-full text-left rounded-md border border-border p-2 text-sm hover:bg-secondary/30" onClick={() => openEntity(e.id)}>
                <div className="font-medium text-foreground truncate">{e.canonical_name}</div>
                <div className="text-xs text-muted-foreground">{entityTypeLabel(e.entity_type)} · {fmtDate(e.updated_at)}</div>
              </button>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Novos registros</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {recentCreated.length === 0 ? <p className="text-sm text-muted-foreground">Sem dados ainda.</p> : recentCreated.map((e) => (
              <button key={e.id} type="button" className="w-full text-left rounded-md border border-border p-2 text-sm hover:bg-secondary/30" onClick={() => openEntity(e.id)}>
                <div className="font-medium text-foreground truncate">{e.canonical_name}</div>
                <div className="text-xs text-muted-foreground">{entityTypeLabel(e.entity_type)} · {fmtDate(e.created_at)}</div>
              </button>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-sm">Recentemente consultadas</CardTitle><CardDescription className="text-xs">Histórico local deste navegador (não simulado).</CardDescription></CardHeader>
          <CardContent className="space-y-2">
            {recentConsulted.length === 0 ? <p className="text-sm text-muted-foreground">Nenhuma consulta registrada ainda.</p> : recentConsulted.map((e) => (
              <button key={e.id} type="button" className="w-full text-left rounded-md border border-border p-2 text-sm hover:bg-secondary/30" onClick={() => openEntity(e.id)}>
                <div className="font-medium text-foreground truncate">{e.canonical_name}</div>
                <div className="text-xs text-muted-foreground">{entityTypeLabel(e.entity_type)}</div>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
