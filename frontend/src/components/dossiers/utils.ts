import type { EntityAliasPayload, EntityIdentifierPayload, EntitySummary } from "@/lib/api/types";

export const ENTITY_TYPE_OPTIONS = [
  { value: "person", label: "Pessoa" },
  { value: "company", label: "Empresa" },
  { value: "economic_group", label: "Grupo econômico / Holding" },
  { value: "institution", label: "Instituição" },
  { value: "other", label: "Outra entidade" },
] as const;

export const PROFILE_STATUS_OPTIONS = [
  { value: "active", label: "Ativo" },
  { value: "pending", label: "Pendente" },
  { value: "archived", label: "Arquivado" },
] as const;

export const VERIFICATION_OPTIONS = [
  { value: "nao_verificado", label: "Não verificado" },
  { value: "em_verificacao", label: "Em verificação" },
  { value: "verificado", label: "Verificado" },
  { value: "contestado", label: "Contestado" },
  { value: "invalido", label: "Inválido" },
] as const;

export const INTERACTION_NATURE_OPTIONS = [
  { value: "declarado", label: "Declarado" },
  { value: "observado", label: "Observado" },
  { value: "interpretado", label: "Interpretado" },
  { value: "a_confirmar", label: "A confirmar" },
] as const;

export const INTERACTION_STATUS_OPTIONS = [
  { value: "registered", label: "Registrado" },
  { value: "confirmed", label: "Confirmado" },
  { value: "needs_review", label: "Requer revisão" },
  { value: "contested", label: "Contestado" },
  { value: "cancelled", label: "Cancelado" },
  { value: "archived", label: "Arquivado" },
] as const;

export const INTERACTION_TYPE_OPTIONS = [
  { value: "meeting", label: "Reunião" },
  { value: "call", label: "Chamada" },
  { value: "email", label: "E-mail" },
  { value: "message", label: "Mensagem" },
  { value: "event", label: "Evento" },
  { value: "visit", label: "Visita" },
  { value: "transaction_contact", label: "Contato transacional" },
  { value: "note", label: "Nota" },
  { value: "other", label: "Outro" },
] as const;

export const TIME_PRECISION_OPTIONS = [
  { value: "exact", label: "Exata" },
  { value: "date", label: "Data" },
  { value: "month", label: "Mês" },
  { value: "approximate", label: "Aproximada" },
  { value: "unknown", label: "Desconhecida" },
] as const;

export function entityTypeLabel(value: string): string {
  return ENTITY_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function profileStatusLabel(value: string): string {
  return PROFILE_STATUS_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function verificationLabel(value: string): string {
  return VERIFICATION_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function interactionNatureLabel(value: string): string {
  return INTERACTION_NATURE_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function interactionStatusLabel(value: string): string {
  return INTERACTION_STATUS_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function interactionTypeLabel(value: string): string {
  return INTERACTION_TYPE_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function timePrecisionLabel(value: string): string {
  return TIME_PRECISION_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

const RECENT_KEY = "scout-dossiers-recent-entities";
const MAX_RECENT = 8;

export function readRecentEntities(): EntitySummary[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as EntitySummary[];
    return Array.isArray(parsed) ? parsed.slice(0, MAX_RECENT) : [];
  } catch {
    return [];
  }
}

export function pushRecentEntity(entity: EntitySummary): void {
  if (typeof window === "undefined") return;
  try {
    const current = readRecentEntities().filter((e) => e.id !== entity.id);
    current.unshift(entity);
    window.localStorage.setItem(RECENT_KEY, JSON.stringify(current.slice(0, MAX_RECENT)));
  } catch {
    /* ignore */
  }
}

export function parseAliasesText(text: string): EntityAliasPayload[] {
  return text
    .split(/\n|,/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map((name) => ({ name, alias_type: "alternate" }));
}

export function aliasesToText(aliases: { name: string }[] | undefined): string {
  return (aliases ?? []).map((a) => a.name).join("\n");
}

export function parseIdentifiersText(text: string): EntityIdentifierPayload[] {
  // one per line: type:value  (or just value -> external_id)
  const out: EntityIdentifierPayload[] = [];
  let idx = 0;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const sep = line.indexOf(":");
    let id_type = "external_id";
    let value = line;
    if (sep > 0) {
      id_type = line.slice(0, sep).trim() || "external_id";
      value = line.slice(sep + 1).trim();
    }
    if (!value) continue;
    out.push({ id_type, value, is_primary: idx === 0 });
    idx += 1;
  }
  return out;
}

export function identifiersToText(
  identifiers: { id_type: string; value: string }[] | undefined,
): string {
  return (identifiers ?? []).map((i) => `${i.id_type}:${i.value}`).join("\n");
}

export function parseProfileDataText(text: string): Record<string, unknown> | null {
  const t = text.trim();
  if (!t) return null;
  try {
    const parsed = JSON.parse(t) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    return null;
  } catch {
    return null;
  }
}

export function profileDataToText(data: Record<string, unknown> | null | undefined): string {
  if (!data || Object.keys(data).length === 0) return "";
  try {
    return JSON.stringify(data, null, 2);
  } catch {
    return "";
  }
}

export const CONNECTION_NATURE_OPTIONS = [
  { value: "declarado", label: "Declarado" },
  { value: "observado", label: "Observado" },
  { value: "inferido", label: "Inferido" },
  { value: "a_confirmar", label: "A confirmar" },
] as const;

export const CONNECTION_STATUS_OPTIONS = [
  { value: "active", label: "Ativa" },
  { value: "needs_review", label: "Requer revisão" },
  { value: "inactive", label: "Inativa" },
  { value: "archived", label: "Arquivada" },
] as const;

export const CONNECTION_VERIFICATION_OPTIONS = [
  { value: "nao_verificado", label: "Não verificado" },
  { value: "verificado", label: "Verificado" },
  { value: "contestado", label: "Contestado" },
] as const;

export const CONNECTION_TIME_PRECISION_OPTIONS = [
  { value: "", label: "—" },
  { value: "exact", label: "Exata" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
  { value: "estimated", label: "Estimada" },
  { value: "unknown", label: "Desconhecida" },
] as const;

export const CONNECTION_DIRECTION_OPTIONS = [
  { value: "", label: "Todas" },
  { value: "outgoing", label: "Saída" },
  { value: "incoming", label: "Entrada" },
  { value: "both", label: "Ambas" },
] as const;

export function connectionNatureLabel(value: string): string {
  return CONNECTION_NATURE_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function connectionStatusLabel(value: string): string {
  return CONNECTION_STATUS_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function connectionVerificationLabel(value: string): string {
  return CONNECTION_VERIFICATION_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

export function connectionTimePrecisionLabel(value: string): string {
  return CONNECTION_TIME_PRECISION_OPTIONS.find((o) => o.value === value)?.label ?? value;
}
