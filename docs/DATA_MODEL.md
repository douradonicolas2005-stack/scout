# DATA_MODEL — SCOUT (Foundation V1.1 + Dossiers D1/D2/D3)

> **Status:** consolidado na Subetapa H (Foundation) e estendido em Dossiers **D1 — Entity Profiles**, **D2 — Research & Evidence** e **D3 — Relationship History** (D3 implementado, validado e publicado). Schema versionado por migrações Alembic aditivas.

## Fonte oficial e migrações
- **Banco:** SQLite (`backend/data/scout.db` por padrão).
- **Migrações:** Alembic (`backend/app/db/migrations`).
  - **`426757a848bb`** — `foundation_b_schema` (15 tabelas de domínio Foundation).
  - **`b7d1e2f3a4c5`** — `dossiers_d1_entity_profiles` (extensão de `entities`, `entity_identifiers`, `entity_aliases`).
  - **D2 (cadeia aditiva):** `c1d2e3f4a5b6` (`research_sources`), `d2e3f4a5b6c7` (`documents` + `document_entity_links`), `e3f4a5b6c7d8` (`extracted_claims` + `claim_entity_links`), `f4a5b6c7d8e9` (`claim_conflicts`), `a5b6c7d8e9f0` (`evidence`).
  - **D3 (aditiva, working tree):** `b6c7d8e9f0a1` — `d3_relationship_history` (`entity_interactions`, filha de `a5b6c7d8e9f0`).
  - Aplicar: `cd backend && .venv/bin/alembic upgrade head`. **Estado local verificado:** head `b6c7d8e9f0a1` (migração D3 aplicada ao DB local).
- **Configuração SQLite (runtime):** `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=5000`.
- **Storage local:** `backend/data/raw/` e `backend/data/documents/` (gitignored; preservação condicionada a licença/termos/configuração/permissões).

## Entidades/tabelas de domínio (22)

| Tabela | Propósito principal | Campos-chave (resumo) |
|---|---|---|
| `sources` | Cadastro de fontes (ingestão) | nome, categoria, `resource_locator`, tipo/auth/ref credencial, frequência, status, tempos, config/permissões/termos, ativo |
| `connectors` | Registro de conectores | `key` (única), nome, versão, capabilities/config schema, status |
| `collection_jobs` | Tarefas de coleta | `source_id`, trigger, status/prioridade, agendamento, tentativas, cancelamento, erro, tempos |
| `collection_runs` | Execuções de jobs | `job_id/source_id`, status, métricas, erro, tempos |
| `raw_records` | Registros brutos coletados | `source_id/run_id`, `external_id`, `content_hash`, tipo, `storage_path`, preservação/licença, metadados, proveniência temporal, `verification_status` |
| `documents` | Documentos/artefatos e referências (D2) | âncoras de proveniência (`source_id`, `raw_record_id`, `research_source_id`, `source_locator`), tipo/origem, metadados, integridade/hash, datas, verificação/acesso/licença/referência-only |
| `extracted_claims` | Afirmações registradas (D2) | texto, `claim_type`/`claim_origin`, verificação/confiança/justificativa, `conflict_status`, vínculos a entidade/fonte/documento/raw_record, versionamento/supersessão e datas |
| `evidence` | Evidências de claims (D2) | tipo e relação (`supports/contests/contextualizes`), âncoras (documento/fonte de pesquisa/raw_record/source), localização/trechos, confiança/verificação e datas |
| `entities` | Entidades/perfis de dossiê (D1) | tipo, nome canônico/normalizado, descrição, `profile_status`, localização primária, `profile_data`/atributos, confiança/verificação, primeira/última visão, origem |
| `entity_identifiers` | Identificadores de entidade (D1) | `entity_id`, tipo, valor, `normalized_value`, primário, metadados, timestamps |
| `entity_aliases` | Nomes alternativos (D1) | `entity_id`, nome, `normalized_name`, tipo de alias, timestamps |
| `research_sources` | Fontes de pesquisa do dossiê (D2) | nome, tipo/domínio/URL, classificação, consulta/verificação, confiabilidade/justificativa, vínculo opcional à fonte de ingestão, metadados |
| `document_entity_links` | Vínculo documento↔entidade (D2) | `document_id`, `entity_id`, papel/notas (N:N) |
| `claim_entity_links` | Vínculo afirmação↔entidade (D2) | `claim_id`, `entity_id`, relevância (N:N) |
| `claim_conflicts` | Conflitos entre afirmações (D2) | par de claims, tipo, descrição, status, detecção/autor, timestamps (registro explícito) |
| `entity_interactions` | Histórico de interações por entidade (D3) | `entity_id`, tipo, título/descrição, `nature` (`declarado|observado|interpretado|a_confirmar`), `status`, temporalidade/precisão, canal/local/participantes, proveniência/referências opcionais (documento/fonte/raw/afirmação/evidência/localizador), confiança/justificativa, verificação, metadados |
| `relationships` | Relações entre entidades (reservado D4) | de/para, tipo, atributos, vínculos a claim/evidência, confiança/verificação, temporalidade |
| `data_changes` | Histórico de alterações | tabela/id alvo, tipo, before/after JSON, razão, vínculos, ator, `changed_at` |
| `processing_events` | Eventos do pipeline | `job_id/run_id`, estágio, status, mensagem/payload, duração, tempo |
| `agent_runs` | Execuções de agentes/LLM | agente, provedor/modelo, propósito, refs I/O, hash, status, uso/erro, tempos |
| `audit_events` | Auditoria | ator, ação, alvo, severidade, detalhes, origem local, `created_at` |

## Convenções de rastreabilidade e semântica
- **Procedência/tempo:** vínculos a fonte/registro/artefatos e campos temporais (`published_at`, `collected_at`, `occurred_at`, `valid_from`/`valid_to`, intervalos) conforme aplicável.
- **Qualidade/versão:** `confidence`, `verification_status`, `version`, `supersedes_claim_id` (claims) e histórico em `data_changes`.
- **Semântica de claim (`claim_type`):** `fato_verificado | declaracao | inferencia | hipotese | previsao | desconhecido`. **Regra:** inferências não promovidas a fato automaticamente.
- **Natureza de interação (D3):** `declarado | observado | interpretado | a_confirmar` (explícita e obrigatória); interpretações/pendências não promovidas a fato automaticamente.
- **Verificação (`verification_status`):** `nao_verificado | em_verificacao | verificado | contestado | invalido` (defaults conservadores).
- **Deduplicação/preservação:** campos/índices em `raw_records` e armazenamento condicionado a permissões/licença/configuração.

## Uso por subetapas
- **E/F/G (Foundation):** Source Registry, pipeline mínimo rastreável, monitoramento/auditoria operacional.
- **Dossiers D1:** `entities` + identificadores/aliases, duplicidades sugeridas sem fusão, rastreabilidade de mutações.
- **Dossiers D2:** `research_sources`, extensões/links de `documents`/`extracted_claims`/`evidence` e `claim_conflicts` para pesquisa/evidências determinísticas com proveniência e estados epistemológicos explícitos.
- **Dossiers D3:** `entity_interactions` para histórico/timeline por entidade com natureza/estado/contexto/proveniência e rastreabilidade; **não utiliza `relationships`** (reservado a D4).
- **Ainda não populados/funcionais no escopo atual:** derivação automática de artefatos a partir de ingestão, `relationships` (uso D4), `agent_runs` e fluxos de inteligência/predição (D4–D6 e evoluções futuras, sujeitas a autorização).

Detalhes do módulo: `docs/modules/dossiers/DOSSIERS_DATA_MODEL.md`.
