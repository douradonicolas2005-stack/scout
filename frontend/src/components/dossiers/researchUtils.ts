export const RESEARCH_SOURCE_TYPES = [
  "site",
  "noticia",
  "registro_publico",
  "documento_institucional",
  "relatorio",
  "base_dados",
  "rede_social",
  "comunicacao",
  "outro",
] as const;

export const RELIABILITY_OPTIONS = [
  { value: "nao_avaliada", label: "Não avaliada" },
  { value: "baixa", label: "Baixa" },
  { value: "media", label: "Média" },
  { value: "alta", label: "Alta" },
  { value: "contestada", label: "Contestada" },
] as const;

export const CLAIM_TYPE_OPTIONS = [
  { value: "declaracao", label: "Declaração" },
  { value: "fato_verificado", label: "Fato verificado" },
  { value: "inferencia", label: "Inferência" },
  { value: "hipotese", label: "Hipótese" },
  { value: "previsao", label: "Previsão" },
  { value: "desconhecido", label: "Desconhecido" },
] as const;

export const EVIDENCE_RELATION_OPTIONS = [
  { value: "supports", label: "Suporta" },
  { value: "contests", label: "Contesta" },
  { value: "contextualizes", label: "Contextualiza" },
] as const;

export const CONFLICT_STATUS_OPTIONS = [
  { value: "open", label: "Aberto" },
  { value: "under_review", label: "Em análise" },
  { value: "resolved", label: "Resolvido" },
  { value: "dismissed", label: "Descartado" },
] as const;

export function labelFor(options: readonly { value: string; label: string }[], value: string | null | undefined): string {
  if (!value) return "—";
  return options.find((o) => o.value === value)?.label ?? value;
}

export function shortId(id: string | null | undefined): string {
  if (!id) return "—";
  return id.length > 10 ? `${id.slice(0, 8)}…` : id;
}
