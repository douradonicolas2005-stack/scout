# API — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H (Foundation) e estendido por Dossiers D1–D3. Contratos implementados, validados (incluindo smoke test de UI de D3) e publicados. Evolução sujeita a aprovação.

## Base
- Local (loopback): `http://127.0.0.1:8000`
- Prefixo: `/api/v1`
- Formato: JSON
- Documentação automática: `/docs` (Swagger UI), `/openapi.json`

## Sistema e saúde

### `GET /api/v1/health`
Liveness/identidade do serviço. **200:** `status`, `service`, `version`, `environment`, `phase` (`foundation-g`), `timestamp`.

### `GET /api/v1/system/info`
Metadados do sistema, configuração e registro das 8 áreas. **200 (`SystemInfoResponse`):** `app_name`, `version`, `phase`, `environment`, `api_version`, `docs_url`, `openapi_url`, `database`, `ollama`, `scheduler` (DB-canonical; desabilitado por padrão), `modules[]` e `timestamp`.

- `modules.dossiers`: `status="in_development"`, `implemented=true` (D1–D3 implementados; D4–D5 pendentes). Demais módulos funcionais de domínio permanecem placeholders.

### `GET /api/v1/db/status`
Estado de conectividade e metadados do banco (leitura real): `connected`, `dialect`, `database_url`, `table_count`, `tables[]`, revisões Alembic, PRAGMAs SQLite, `error`, `timestamp`. Aplicar migrações: `cd backend && .venv/bin/alembic upgrade head`.

### `GET /api/v1/system/audit-events`
Lista eventos de auditoria recentes (`audit_events`). **Query:** `limit` (1–200, default 50), `target_type`, `target_id`, `action`. **200:** `AuditEventListResponse`.

## Ingestão — conectores e Source Registry (Subetapa E)
- **`GET /api/v1/ingestion/connectors`** / **`GET /api/v1/ingestion/connectors/{connector_key}`** — conectores registrados (built-in `rss_atom`, read-only, limites conservadores).
- **`POST|GET|PATCH /api/v1/ingestion/sources`** e **`GET /api/v1/ingestion/sources/{source_id}`** — cadastro/consulta/atualização de fontes.
- **`POST /api/v1/ingestion/sources/{source_id}/test-connection`** — teste real de conexão/leitura mínima com rastreabilidade (`audit_events`, `processing_events stage=connection_test`).

## Ingestão — jobs, runs e pipeline (Subetapa F)
Execução controlada e rastreável de coleta mínima (estado canônico no banco; scheduler conservador desabilitado por padrão).

- **Jobs:** `POST /api/v1/ingestion/jobs`, `GET /api/v1/ingestion/jobs`, `GET /api/v1/ingestion/jobs/{job_id}`, `POST /api/v1/ingestion/jobs/{job_id}/run`, `GET /api/v1/ingestion/jobs/{job_id}/runs`.
- **Runs/eventos:** `GET /api/v1/ingestion/runs/{run_id}`, `GET /api/v1/ingestion/runs/{run_id}/events`.
- **Comportamento:** coleta real via conector, normalização/validação/deduplicação básica, persistência de `raw_records` e `data_changes`, `processing_events` por estágio, preservação condicional de original, retries conservadores e atualização de estados/métricas.

## Monitoramento operacional (Subetapa G, mínimo)
UI **System** consome contratos acima para visão de conectores/fontes/jobs/runs/eventos e auditoria com controles mínimos reais e estados sem simulação.

## Dossiers (D1–D3)

Base: `/api/v1/dossiers` (detalhes em `docs/modules/dossiers/DOSSIERS_API.md`). Determinístico/manual-first, local-first, rastreável, sem fusão automática, sem promoção automática a fato e sem uso de `relationships` (reservado a D4).

### D1 — Entity Profiles
- **`POST /entities`** (`201`), **`GET /entities`** (pesquisa/filtros/paginação), **`GET /entities/{entity_id}`**, **`PATCH /entities/{entity_id}`**, **`GET /entities/{entity_id}/duplicate-candidates`** (somente leitura, sem fusão).

### D2 — Research & Evidence
- **Fontes de pesquisa:** `POST /research-sources`, `GET /research-sources`, `GET/PATCH /research-sources/{source_id}`.
- **Documentos:** `POST /entities/{entity_id}/documents`, `GET /entities/{entity_id}/documents`, `GET/PATCH /documents/{document_id}`, `POST /documents/{document_id}/entities` (âncora de proveniência obrigatória).
- **Afirmações:** `POST /entities/{entity_id}/claims`, `GET /entities/{entity_id}/claims`, `GET/PATCH /claims/{claim_id}` (classificação epistemológica/verificação/justificativa).
- **Conflitos:** `POST /claims/{claim_id}/conflicts`, `PATCH /claims/{claim_id}/conflicts/{conflict_id}`, `GET /entities/{entity_id}/conflicts`.
- **Evidências:** `POST /claims/{claim_id}/evidence`, `GET /claims/{claim_id}/evidence`, `GET/PATCH /evidence/{evidence_id}` (âncora rastreável).
- **Workspace:** `GET /entities/{entity_id}/research/summary`.

### D3 — Relationship History (interações/timeline)
- **`POST /entities/{entity_id}/interactions`** (`201`) — cria interação com natureza obrigatória (`declarado|observado|interpretado|a_confirmar`), temporalidade/contexto e proveniência/referências opcionais validadas.
- **`GET /entities/{entity_id}/interactions`** — lista/timeline com filtros (`q`, `interaction_type`, `nature`, `status`, período), ordenação e paginação.
- **`GET /interactions/{interaction_id}`** / **`PATCH /interactions/{interaction_id}`** — detalhe e atualização explícita rastreável.
- **`GET /entities/{entity_id}/interactions/summary`** — resumo determinístico (contagens, distribuições, pendências, período).

## Fora de escopo atual (pendente de autorização)
- CRUD completo de fontes e controles operacionais avançados no frontend; monitoramento analítico ampliado.
- Evolução do pipeline para derivação automática de `documents`/claims/evidências/entidades/relacionamentos e encaminhamento para inteligência/predição.
- Dossiers D4–D6 (Connections/`relationships`, Strategic Insights, consolidação), fusão automática, derivação/importação automática de interações, upload remoto/integrações comerciais ou APIs pagas obrigatórias.
- APIs/contratos dos demais módulos funcionais de domínio (Radar, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control).
