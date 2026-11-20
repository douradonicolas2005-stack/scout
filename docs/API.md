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
Metadados do sistema, configuração de alto nível e registro das 8 áreas funcionais.

**Resposta 200 (`SystemInfoResponse`, campos principais):**
- `app_name`, `version`, `phase` (`foundation-g`), `environment`
- `api_version`: `"v1"`, `docs_url`, `openapi_url`
- `database`: `"sqlite"`
- `ollama`: `{ base_url, model, mode: "abstraction-availability-only" }`
- `scheduler`: `{ enabled, max_concurrent_jobs, state }` — estado canônico no banco; quando desabilitado `db-canonical-ready`, quando habilitado `db-canonical` (dispatch conservador, sem paralelismo pesado).
- `modules[]`: 8 itens `{ key, label, path, status, implemented }`
  - `dossiers`: `status="in_development"`, `implemented=true` (D1 — Entity Profiles e D2 — Research & Evidence entregues; D3–D5 pendentes)
  - demais (`radar`, `knowledge-graph`, `predictions`, `scenario-lab`, `action-center`, `agent-control`, `system`): `placeholder` / `implemented=false` (Foundation)
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

## Dossiers (D1 + D2, implementado)

Base: `/api/v1/dossiers` (detalhes em `docs/modules/dossiers/DOSSIERS_API.md`).

### D1 — Entity Profiles
- **`POST /entities`** (`201`) — cria entidade/perfil com normalização e rastreabilidade (`audit_events`/`data_changes`).
- **`GET /entities`** — lista/pesquisa local (filtros: `q`, `entity_type`, `profile_status`, `verification_status`, `updated_from/to`, `sort`, paginação).
- **`GET /entities/{entity_id}`** — detalhe (perfil + identificadores/aliases).
- **`PATCH /entities/{entity_id}`** — atualização parcial com rastreabilidade.
- **`GET /entities/{entity_id}/duplicate-candidates`** — sugestões de duplicidade (somente leitura, sem fusão automática).

### D2 — Research & Evidence (determinístico/manual-first)
- **Fontes de pesquisa:** `POST /research-sources`, `GET /research-sources`, `GET/PATCH /research-sources/{source_id}`.
- **Documentos:** `POST /entities/{entity_id}/documents`, `GET /entities/{entity_id}/documents`, `GET/PATCH /documents/{document_id}`, `POST /documents/{document_id}/entities` (registro com âncora de proveniência e vínculos a entidades).
- **Afirmações:** `POST /entities/{entity_id}/claims`, `GET /entities/{entity_id}/claims`, `GET/PATCH /claims/{claim_id}` (classificação epistemológica/verificação/justificativa, sem promoção automática a fato).
- **Conflitos:** `POST /claims/{claim_id}/conflicts`, `PATCH /claims/{claim_id}/conflicts/{conflict_id}`, `GET /entities/{entity_id}/conflicts` (registro/atualização explícita, sem resolução automática).
- **Evidências:** `POST /claims/{claim_id}/evidence`, `GET /claims/{claim_id}/evidence`, `GET/PATCH /evidence/{evidence_id}` (relação suporta/contesta/contextualiza, âncoras/localização rastreável).
- **Workspace:** `GET /entities/{entity_id}/research/summary` (indicadores determinísticos).

## Fora de escopo atual (pendente de autorização)
- CRUD completo de fontes e controles operacionais avançados no frontend; filtros/paginação/métricas consolidadas e monitoramento analítico ampliado.
- Evolução do pipeline de ingestão para derivação automática de `documents`, extração/claims/evidências/entidades/relacionamentos e encaminhamento para inteligência/predição.
- Dossiers D3–D5 (Relationship History, Connections, Strategic Insights) e D6; fusão automática de entidades; upload remoto/integrações comerciais obrigatórias.
- APIs/contratos dos demais módulos funcionais de domínio (Radar, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control).
