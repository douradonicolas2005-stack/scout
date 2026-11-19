# DATA_MODEL — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H. Schema implementado na Subetapa B e utilizado nas Subetapas E/F/G **sem alteração de migração** (validação final).

## Fonte oficial e migrações
- **Banco:** SQLite (`backend/data/scout.db` por padrão).
- **Migrações:** Alembic (`backend/app/db/migrations`).
  - **Revisão:** `426757a848bb` — `foundation_b_schema` (cria as 15 tabelas de domínio e índices).
  - Aplicar: `cd backend && .venv/bin/alembic upgrade head`
- **Configuração SQLite (runtime):** `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=5000` (aplicados na conexão).
- **Storage local:** `backend/data/raw/` e `backend/data/documents/` (gitignored; preservação condicionada a licença/termos/configuração/permissões).

## Entidades implementadas (15)

| Tabela | Propósito principal | Campos-chave (resumo) |
|---|---|---|
| `sources` | Cadastro de fontes | nome, categoria, `resource_locator`, tipo/auth/ref credencial, frequência, status, `last/next_collect_at`, config/permissões/termos, ativo |
| `connectors` | Registro de conectores | `key` (única), nome, versão, capabilities/config schema, status |
| `collection_jobs` | Tarefas de coleta | `source_id`, trigger, status/prioridade, agendamento, tentativas, cancelamento, erro, tempos |
| `collection_runs` | Execuções de jobs | `job_id/source_id`, status, métricas (itens encontrados/armazenados/deduplicados/inválidos, bytes), erro, tempos |
| `raw_records` | Registros brutos coletados | `source_id/run_id`, `external_id`, `content_hash`, tipo, `storage_path`, preservação/licença, metadados, proveniência temporal e `verification_status` |
| `documents` | Documentos/artefatos | `source_id/raw_record_id`, título/mime/path/checksum/tamanho/idioma, metadados e datas |
| `extracted_claims` | Afirmações extraídas | texto/estrutura, `claim_type`, `confidence`, `verification_status`, `version`, `supersedes_claim_id`, vínculos e datas de procedência/validade |
| `evidence` | Evidências de claims | `claim_id/source_id/raw_record_id`, locator/snippet/note, confiança, verificação e datas |
| `entities` | Entidades do conhecimento | tipo, nome canônico/normalizado, atributos, confiança/verificação, primeira/última visão, origem |
| `relationships` | Relações entre entidades | de/para, tipo, atributos, vínculos a claim/evidência, confiança/verificação, temporalidade |
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

## Uso por subetapas (sem novas migrações)
- **E:** `connectors`/`sources` para Source Registry; `audit_events` e `processing_events` (`stage=connection_test`) para rastreabilidade de operações e testes de conexão.
- **F:** `collection_jobs`/`collection_runs` como estado/histórico canônico; `raw_records` com proveniência/deduplicação e preservação condicional; `processing_events` por estágio (`job`, `identify`, `collect`, `normalize_validate_dedupe_store`, `run`); `data_changes` para persistências (ex.: criação de `raw_records`); atualização de `sources.last_collected_at`.
- **G:** leitura operacional para monitoramento/UI (jobs/runs/eventos) e consulta de `audit_events` via API (`GET /api/v1/system/audit-events`) para rastreabilidade recente.
- **Ainda não populados pelo fluxo mínimo:** `documents` derivados, `extracted_claims`, `evidence`, `entities`, `relationships`, `agent_runs` (escopo de etapas futuras conforme aprovação).
