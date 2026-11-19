# API — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H (contratos implementados e validados em A–G; evolução sujeita a aprovação).

## Base
- Local (loopback): `http://127.0.0.1:8000`
- Prefixo: `/api/v1`
- Formato: JSON
- Documentação automática: `/docs` (Swagger UI), `/openapi.json`

## Sistema e saúde

### `GET /api/v1/health`
Liveness/identidade do serviço.

**Resposta 200 (`HealthResponse`):** `status`, `service`, `version`, `environment`, `phase` (`foundation-g`), `timestamp`.

### `GET /api/v1/system/info`
Metadados do sistema, configuração de alto nível e registro das 8 áreas funcionais (todas `placeholder` na Foundation).

**Resposta 200 (`SystemInfoResponse`, campos principais):**
- `app_name`, `version`, `phase` (`foundation-g`), `environment`
- `api_version`: `"v1"`, `docs_url`, `openapi_url`
- `database`: `"sqlite"`
- `ollama`: `{ base_url, model, mode: "abstraction-availability-only" }`
- `scheduler`: `{ enabled, max_concurrent_jobs, state }` — estado canônico no banco; quando desabilitado `db-canonical-ready`, quando habilitado `db-canonical` (dispatch conservador, sem paralelismo pesado).
- `modules[]`: 8 itens `{ key, label, path, status: "placeholder", implemented: false }`
  - `radar`, `dossiers`, `knowledge-graph`, `predictions`, `scenario-lab`, `action-center`, `agent-control`, `system`
- `timestamp`

### `GET /api/v1/db/status`
Estado de conectividade e metadados do banco (leitura real): `connected`, `dialect`, `database_url`, `table_count`, `tables[] { name, row_count }`, `alembic_revision`/`alembic_revisions[]`, PRAGMAs SQLite (`foreign_keys`, `journal_mode`, `busy_timeout`), `error`, `timestamp`.

> Observação: para o schema completo da Foundation, aplicar migrações: `cd backend && .venv/bin/alembic upgrade head`.

### `GET /api/v1/system/audit-events` (Subetapa G)
Lista eventos de auditoria recentes (`audit_events`) para rastreabilidade operacional.

**Query params (opcionais):** `limit` (1–200, default 50), `target_type`, `target_id`, `action`.

**Resposta 200 (`AuditEventListResponse`):** `items[] { id, actor_type, actor_id, action, target_type, target_id, severity, details_json, ip_or_origin, created_at }`.

## Ingestão — conectores e Source Registry (Subetapa E)

### Conectores
- **`GET /api/v1/ingestion/connectors`** → lista conectores registrados/built-in sincronizados.
- **`GET /api/v1/ingestion/connectors/{connector_key}`** → detalhe do conector (404 se não encontrado).

**Conector built-in (referência):** `rss_atom` (RSS/Atom, somente leitura; fetch mínimo de metadados/títulos, limite rígido de 5 itens, timeouts/tamanho de resposta limitados).

### Fontes (sources)
- **`POST /api/v1/ingestion/sources`** (`201`) — cria fonte (valida `connection_type` e `config_json` quando aplicável).
- **`GET /api/v1/ingestion/sources`** — lista fontes (`active_only=true|false`).
- **`GET /api/v1/ingestion/sources/{source_id}`** — detalhe.
- **`PATCH /api/v1/ingestion/sources/{source_id}`** — atualização parcial e ativação/desativação.
- **`POST /api/v1/ingestion/sources/{source_id}/test-connection`** — **teste real** de conexão/leitura mínima (sem simulação, sem pipeline/jobs/runs de coleta). Registra `audit_events` e `processing_events` (`stage=connection_test`).

## Ingestão — jobs, runs e pipeline (Subetapa F)

> **Escopo implementado:** execução controlada e rastreável de coleta mínima (manual e/ou via scheduler quando habilitado), com estado canônico no banco. Não inclui CRUD completo de fontes no frontend, controles operacionais avançados, inferência automática, promoção de inferência a fato, nem módulos funcionais de domínio.

### Jobs de coleta (`collection_jobs`)
- **`POST /api/v1/ingestion/jobs`** (`201`) — cria job para uma fonte (`source_id`, `trigger`, `requested_by`, `scheduled_for`, `max_attempts`, `execute_now`). Retorna `{ job, run? }`; se `execute_now=true` (padrão), executa imediatamente o pipeline controlado e inclui o run resultante.
- **`GET /api/v1/ingestion/jobs`** — lista jobs (filtros: `source_id`, `status`).
- **`GET /api/v1/ingestion/jobs/{job_id}`** — detalhe do job.
- **`POST /api/v1/ingestion/jobs/{job_id}/run`** — executa/retoma execução controlada do job (cria novo run para a tentativa). Retorna `{ job, run }`.
- **`GET /api/v1/ingestion/jobs/{job_id}/runs`** — histórico de runs do job.

### Runs e eventos (`collection_runs`, `processing_events`)
- **`GET /api/v1/ingestion/runs/{run_id}`** — detalhe do run (status, contagens `items_found/stored/deduplicated/invalid`, bytes, métricas, erro/timestamps).
- **`GET /api/v1/ingestion/runs/{run_id}/events`** — eventos de processamento do run em ordem temporal (estágios como `job`, `identify`, `collect`, `normalize_validate_dedupe_store`, `run`).

### Comportamento do pipeline mínimo
- Coleta real via conector registrado da fonte (ex.: `rss_atom`) com limites conservadores.
- Normalização/validação básica e deduplicação por `source_id + external_id` ou `content_hash`.
- Persistência de `raw_records` com metadados/proveniência mínima; `data_changes` para registros criados.
- **Armazenamento do original condicionado:** preserva arquivo bruto em `backend/data/raw/<source_id>/` e marca `raw_records.is_preserved/storage_path` somente quando permitido por configuração/permissões/licença (`config_json.preserve_raw` ou `permissions_json.allow_storage/preserve_raw`); caso contrário, não armazena corpo/original em disco.
- Atualiza `sources.last_collected_at`, estados do job/run e registra `processing_events`; política de retry conservadora (`attempt < max_attempts` → `pending` com reagendamento).

### Scheduler (APScheduler, conservador)
- Background, **desabilitado por padrão** (`scheduler_enabled=false`), sem paralelismo pesado (`max_concurrent_jobs` efetivo mínimo 1).
- **Estado canônico no banco:** jobs `pending` elegíveis (`scheduled_for` nulo ou vencido) são despachados por tick; reidratação controlada no startup quando habilitado. Falhas não promovem inferência nem executam ações externas não autorizadas.

## Monitoramento operacional (Subetapa G, mínimo)
- A área **System** (frontend) consome os contratos acima para visão de conectores/fontes/jobs/runs/eventos e auditoria, com controles mínimos reais (teste de conexão, criação/execução de jobs) e estados loading/erro/vazio/sucesso, sem simulações.

## Fora de escopo atual (pós-Foundation, sujeito a aprovação)
- CRUD completo de fontes e controles operacionais avançados no frontend; filtros/paginação/métricas consolidadas e monitoramento analítico ampliado.
- Evolução do pipeline para `documents`, extração/claims/evidências/entidades/relacionamentos e encaminhamento para inteligência/predição.
- APIs/contratos de módulos funcionais de domínio (Radar, Dossiers, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control).
