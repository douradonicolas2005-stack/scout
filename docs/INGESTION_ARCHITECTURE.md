# INGESTION_ARCHITECTURE — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H (Subetapas E/F/G implementadas e validadas; evolução sujeita a aprovação).

## Componentes

### Source Registry (implementado — E)
- Cadastro, consulta, atualização e ativação/desativação de **fontes** (`sources`) e registro/sincronização de **conectores** (`connectors`) via API (`/api/v1/ingestion/*`).
- Campos: identidade/descrição/categoria, `resource_locator`, `connection_type`, refs de auth (`auth_method`, `auth_credential_ref` — sem segredos em claro), frequência, status/ativo, `config_json`, `permissions_json`, `terms_conditions`, timestamps.
- Validações: conector conhecido, configuração validada pelo conector quando aplicável, coerência básica de ativação/status.

### Connectors — plugáveis (implementado — E)
- Interface padrão em `app/ingestion/connectors/base.py` (`validate_config`, `check_availability`, `test_connection`, `collect`, `describe_capabilities`).
- Registro em memória (`app/ingestion/registry.py`) e bootstrap/sincronização de metadados em banco (`app/ingestion/bootstrap.py`).
- **Conector de referência real:** `rss_atom` (`app/ingestion/connectors/rss_atom.py`) — RSS 2.0/Atom, somente leitura, metadados/títulos/links/ids/datas, limite rígido **máx. 5 itens**, timeout/tamanho de resposta limitados. `test_connection` (HTTP real, sem simulação) e `collect` para pipeline mínimo. Conteúdo externo tratado como **dado não confiável**.

### Collectors & Scheduler (implementado — F, conservador)
- **APScheduler (Background)** em `app/ingestion/scheduler.py`, desabilitado por padrão (`scheduler_enabled=false`), sem paralelismo pesado (`max_concurrent_jobs` mínimo efetivo 1), tick de dispatch com coalescência.
- **Estado canônico no banco:** jobs elegíveis são `collection_jobs` com `status=pending` e `scheduled_for` nulo ou vencido (ordenados por prioridade/agenda/criação). O scheduler não mantém fila canônica em memória.
- **Reidratação controlada:** no startup (quando habilitado), executa dispatch para processar pendências persistidas; processamento síncrono/controlado por tick.
- **Execução manual:** criação/execução de jobs via API (`execute_now`, `/jobs/{id}/run`) independente do scheduler.

### Pipeline mínimo (implementado — F)
- Implementação: `app/ingestion/collection.py` (endpoints em `app/api/v1/endpoints/collection.py`).
- Fluxo executado: identificação (fonte+conector/config) → criação de `collection_job`/`collection_run` → coleta (`connector.collect`) → normalização/validação básica → deduplicação (`source_id + external_id` ou `content_hash`) → persistência de `raw_records` → registro de `data_changes` e `processing_events` → atualização de estados/`last_collected_at`.
- **Armazenamento do original:** condicionado a permissão/licença/config (`config_json.preserve_raw` ou `permissions_json.allow_storage/preserve_raw`). Quando permitido, grava JSON em `backend/data/raw/<source_id>/` e marca `raw_records.is_preserved/storage_path`; caso contrário, mantém apenas metadados/registro (sem corpo bruto em disco).
- **Erros/retries:** falhas registradas em run/job/eventos; política conservadora de retry (`attempt < max_attempts` → `pending` com reagendamento), sem ações externas não autorizadas.
- **Fora do escopo implementado:** `documents` derivados, extração/claims/evidências/entidades/relacionamentos, encaminhamento para processamento de inteligência/predição e operação analítica completa.

## Source Manager e monitoramento (implementado — G, mínimo)
- **UI (área System):** `frontend/src/pages/SystemPage.tsx` consome contratos reais para listar conectores/fontes, jobs, runs e eventos de processamento, além de auditoria recente, com estados loading/erro/vazio/sucesso.
- **Controles mínimos suportados:** teste de conexão de fonte, criação de job (`execute_now` opcional) e execução de job existente; atualização/inspeção de histórico e erros/eventos.
- **API de suporte:** leitura de `audit_events` via `GET /api/v1/system/audit-events` (`app/api/v1/endpoints/audit.py`) complementa endpoints de ingestão.
- **Fora do escopo G:** CRUD completo de fontes no frontend, controles avançados de operação/agendamento/filtragem consolidada, UI dedicada fora de System e monitoramento analítico completo.

## Rastreabilidade
- **Implementado:** `audit_events` (criação/atualização/teste de fontes, criação de jobs); `processing_events` (testes de conexão e estágios de job/run: `job`, `identify`, `collect`, `normalize_validate_dedupe_store`, `run`); `collection_jobs`, `collection_runs`, `raw_records` e `data_changes` no fluxo de coleta mínima.
- **Parcial/futuro:** uso operacional completo de `documents`, enriquecimento de metadados de publicação/ocorrência/validade quando disponíveis, histórico/monitoramento operacional ampliado e controles avançados.

## Decisão 4 — conector/fonte de referência real
- **Situação:** URLs fornecidas anteriormente eram inválidas/placeholders. Com autorização explícita do usuário para prosseguir automaticamente sem confirmação, foi **auto-aplicado** um recurso público de referência para testes/coleta real local: **`https://www.w3.org/news/feed/`** (RSS, público, W3C News).
- **Restrições aplicadas:** leitura somente de metadados/títulos, **máx. 5 itens**, timeouts/limites, sem preservação de corpo/conteúdo completo nos testes/pipeline padrão.
- **Ação recomendada:** confirmar explicitamente se este recurso deve permanecer autorizado para continuidade ou substituí-lo por outro RSS/Atom/HTTP GET autorizado.
