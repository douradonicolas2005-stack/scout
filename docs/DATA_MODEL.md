# DATA_MODEL — SCOUT (Foundation V1.1 + Dossiers D1/D2)

> **Status:** consolidado na Subetapa H (Foundation) e estendido em Dossiers **D1 — Entity Profiles** e **D2 — Research & Evidence** (autorizados, implementados no working tree). Schema versionado por migrações Alembic aditivas.

## Fonte oficial e migrações
- **Banco:** SQLite (`backend/data/scout.db` por padrão).
- **Migrações:** Alembic (`backend/app/db/migrations`).
  - **`426757a848bb`** — `foundation_b_schema` (cria as 15 tabelas de domínio Foundation e índices).
  - **`b7d1e2f3a4c5`** — `dossiers_d1_entity_profiles` (filha de `426757a848bb`; extensão aditiva de `entities` e criação de `entity_identifiers`, `entity_aliases`).
  - **D2 (cadeia aditiva após `b7d1e2f3a4c5`, validadas em DB temporário):**
    - `c1d2e3f4a5b6` — `d2_research_sources` (cria `research_sources`).
    - `d2e3f4a5b6c7` — `d2_documents_extend_and_links` (estende `documents`, cria `document_entity_links`).
    - `e3f4a5b6c7d8` — `d2_claims_extend_and_links` (estende `extracted_claims`, cria `claim_entity_links`).
    - `f4a5b6c7d8e9` — `d2_claim_conflicts` (cria `claim_conflicts`).
    - `a5b6c7d8e9f0` — `d2_evidence_extend` (estende `evidence`).
  - Aplicar: `cd backend && .venv/bin/alembic upgrade head` (aplicação no DB local das revisões D2 pendente de autorização explícita no estado atual do working tree).
- **Configuração SQLite (runtime):** `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=5000` (aplicados na conexão).
- **Storage local:** `backend/data/raw/` e `backend/data/documents/` (gitignored; preservação condicionada a licença/termos/configuração/permissões).

## Entidades/tabelas de domínio (21)

### Foundation (15)

| Tabela | Propósito principal | Campos-chave (resumo) |
|---|---|---|
| `sources` | Cadastro de fontes | nome, categoria, `resource_locator`, tipo/auth/ref credencial, frequência, status, `last/next_collect_at`, config/permissões/termos, ativo |
| `connectors` | Registro de conectores | `key` (única), nome, versão, capabilities/config schema, status |
| `collection_jobs` | Tarefas de coleta | `source_id`, trigger, status/prioridade, agendamento, tentativas, cancelamento, erro, tempos |
| `collection_runs` | Execuções de jobs | `job_id/source_id`, status, métricas (itens encontrados/armazenados/deduplicados/inválidos, bytes), erro, tempos |
| `raw_records` | Registros brutos coletados | `source_id/run_id`, `external_id`, `content_hash`, tipo, `storage_path`, preservação/licença, metadados, proveniência temporal e `verification_status` |
| `documents` | Documentos/artefatos e referências de pesquisa (D2: estendida) | âncoras de proveniência (`source_id`/ingestão, `raw_record_id`, `research_source_id`, `source_locator`), tipo/origem, metadados, integridade/hash, datas (publicação/ocorrência/captura/coleta), verificação/acesso/licença/referência-only |
| `extracted_claims` | Afirmações registradas (D2: estendida) | texto, `claim_type`/`claim_origin`, verificação/confiança/justificativa, `conflict_status`, vínculos a entidade/fonte/documento/raw_record, versionamento/supersessão e datas |
| `evidence` | Evidências de claims (D2: estendida) | tipo e relação (`supports/contests/contextualizes`), âncoras (documento/fonte de pesquisa/raw_record/source), localização/trechos, confiança/verificação e datas |
| `entities` | Entidades do conhecimento / perfis de dossiê (D1) | tipo, nome canônico/normalizado, descrição, `profile_status`, localização primária, `profile_data`/atributos, confiança/verificação, primeira/última visão, origem |
| `entity_identifiers` | Identificadores de entidade (D1) | `entity_id`, tipo, valor, `normalized_value`, primário, metadados, timestamps |
| `entity_aliases` | Nomes alternativos de entidade (D1) | `entity_id`, nome, `normalized_name`, tipo de alias, timestamps |
| `research_sources` | Fontes de pesquisa/referência de dossiê (D2) | nome, tipo/domínio/URL, classificação, consulta/verificação, confiabilidade/justificativa, vínculo opcional à fonte de ingestão, metadados |
| `document_entity_links` | Vínculo documento↔entidade (D2) | `document_id`, `entity_id`, papel/notas (N:N) |
| `claim_entity_links` | Vínculo afirmação↔entidade (D2) | `claim_id`, `entity_id`, relevância (N:N) |
| `claim_conflicts` | Conflitos entre afirmações (D2) | par de claims, tipo, descrição, status, detecção/autor, timestamps (registro explícito, sem resolução automática) |
| `relationships` | Relações entre entidades | de/para, tipo, atributos, vínculos a claim/evidência, confiança/verificação, temporalidade (uso de domínio previsto em D4) |
| `data_changes` | Histórico de alterações | tabela/id alvo, tipo, before/after JSON, razão, vínculos a run/evento, ator, `changed_at` |
| `processing_events` | Eventos do pipeline | `job_id/run_id`, estágio, status, mensagem/payload, duração, tempo |
| `agent_runs` | Execuções de agentes/LLM | agente, provedor/modelo, propósito, refs I/O, hash, status, uso/erro, tempos |
| `audit_events` | Auditoria | ator, ação, alvo, severidade, detalhes, origem local, `created_at` |

## Convenções de rastreabilidade e semântica
- **Procedência/tempo:** `source_id`/vínculos, `published_at`, `collected_at`, `occurred_at`, `valid_from`/`valid_to` conforme aplicável.
- **Qualidade/versão:** `confidence`, `verification_status`, `version`, `supersedes_claim_id` (claims) e histórico em `data_changes`.
- **Semântica de claim (`claim_type`):** `fato_verificado | declaracao | inferencia | hipotese | previsao | desconhecido`.
  - **Regra:** inferências **não** são promovidas a fato automaticamente (exige ação/fluxo de controle explícito; sem promoção automática no sistema).
- **Verificação (`verification_status`):** `nao_verificado | em_verificacao | verificado | contestado | invalido` (defaults conservadores).
- **Deduplicação (base):** índices/campos para `(source_id, external_id)` e `content_hash` em `raw_records`; políticas efetivas aplicadas no pipeline mínimo.
- **Preservação:** `is_preserved`/`storage_path`/`license_note` em registros brutos; armazenamento condicionado a permissões/licença/configuração.

## Uso por subetapas
- **E:** `connectors`/`sources` para Source Registry; `audit_events` e `processing_events` (`stage=connection_test`) para rastreabilidade de operações e testes de conexão.
- **F:** `collection_jobs`/`collection_runs` como estado/histórico canônico; `raw_records` com proveniência/deduplicação e preservação condicional; `processing_events` por estágio (`job`, `identify`, `collect`, `normalize_validate_dedupe_store`, `run`); `data_changes` para persistências (ex.: criação de `raw_records`); atualização de `sources.last_collected_at`.
- **G:** leitura operacional para monitoramento/UI (jobs/runs/eventos) e consulta de `audit_events` via API (`GET /api/v1/system/audit-events`) para rastreabilidade recente.
- **Dossiers D1 (Entity Profiles):** `entities` estendida como perfil canônico, com `entity_identifiers`/`entity_aliases` para pesquisa e detecção de duplicidades; mutações registram `audit_events` (`dossier.entity.create/update`) e `data_changes` (`entities`), sem fusão automática.
- **Dossiers D2 (Research & Evidence):** `research_sources`, extensões de `documents`/`extracted_claims`/`evidence` e vínculos N:N/conflitos (`document_entity_links`, `claim_entity_links`, `claim_conflicts`) para registro determinístico/manual de fontes, documentos, afirmações, evidências e conflitos com proveniência, estados epistemológicos/verificação e rastreabilidade (`audit_events`/`data_changes`/`processing_events`). Sem promoção automática de inferência a fato e sem derivação automática a partir de ingestão.
- **Ainda não populados/funcionais no escopo atual:** derivação automática de `documents`/`extracted_claims`/`evidence` a partir do pipeline de ingestão, `relationships` (uso D4), `agent_runs` e fluxos de inteligência/predição (escopo de subetapas futuras conforme aprovação). Detalhes do módulo: `docs/modules/dossiers/DOSSIERS_DATA_MODEL.md`.
