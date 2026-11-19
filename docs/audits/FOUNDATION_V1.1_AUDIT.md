# Relatório de Auditoria Técnica — SCOUT Foundation V1.1

- **Data da auditoria:** 2026-11-19
- **Repositório:** `douradonicolas2005-stack/scout` (`https://github.com/douradonicolas2005-stack/scout`)
- **Branch/commit auditado (estado final):** `main` em `afd481e` (`docs: confirm Decisao 4 W3C feed as authorized reference source`), rastreando `origin/main`
- **Diretório auditado:** `/Users/nicolasdrumonddourado/Documents/Default Project/scout`
- **Escopo:** Foundation V1.1, Subetapas A–H (auditoria técnica Etapas A–J solicitada)
- **Classificação final:** **APROVADA COM RESSALVAS**

> **Nota de integridade do registro:** a coleta de evidências e validações técnicas foi realizada em modo somente leitura. Após a conclusão da auditoria, e mediante autorização explícita do usuário, foi aplicada apenas a confirmação documental da Decisão 4 (W3C) com commit/push `afd481e` (atualização de `README.md`, `docs/PROJECT_STATUS.md`, `docs/ARCHITECTURE.md`, `docs/INGESTION_ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/SECURITY.md` e anotações em `backend/tests/unit/test_ingestion_registry.py`, `backend/tests/unit/test_collection_pipeline.py`). Este relatório é a única criação adicional autorizada, em `docs/audits/FOUNDATION_V1.1_AUDIT.md`, sem commit/push automático.

---

## 1. Escopo, objetivos e critérios

### 1.1 Objetivo
Verificar, com base em evidências, o estado da Foundation V1.1 do SCOUT (estrutura, backend/API, banco/modelo, ingestão/pipeline/scheduler, frontend/integração, segurança, consistência documentação-código e validações), sem presumir funcionalidade a partir de documentação e sem avançar escopo (ex.: Dossiers/módulos de domínio).

### 1.2 Escopo incluído (Etapas A–J)
- **A.** Levantamento de repositório, estrutura e artefatos.
- **B.** Ambiente local, dependências/configurações e estado operacional observável.
- **C.** Backend, API e contratos implementados.
- **D.** Banco de dados, migrações, schema, modelo e semântica.
- **E.** Ingestão, conectores, pipeline, scheduler e rastreabilidade.
- **F.** Frontend, Design System, navegação e integração com API.
- **G.** Consistência entre código, contratos e documentação.
- **H.** Segurança, limites operacionais e controles.
- **I.** Execução/revisão de validações disponíveis e registro de resultados/limitações.
- **J.** Consolidação de achados, classificação e recomendações.

### 1.3 Fora de escopo
- Implementação/correção de funcionalidades de domínio (Radar, Dossiers, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control completos).
- Alterações de schema/migração, ativação de scheduler, coletas externas adicionais, instalações, commits/push (exceto ação posterior explicitamente autorizada para Decisão 4) e qualquer modificação não autorizada.

---

## 2. Ambiente de execução e contexto operacional

### 2.1 Fatos observados — ambiente
| Item | Evidência observada |
|---|---|
| Sistema operacional/arquitetura | macOS 15.7.3 (`sw_vers -productVersion`), `arm64` (`uname -m`) |
| Python (ambiente do backend) | `backend/.venv/bin/python --version` → `Python 3.9.6` |
| Node.js / npm | `node --version` → `v26.5.0`; `npm --version` → `11.17.0` |
| Diretório de trabalho | `/Users/nicolasdrumonddourado/Documents/Default Project/scout` |
| Git | `main...origin/main` limpo antes da criação deste relatório; HEAD `afd481e` (após confirmação autorizada da Decisão 4); remoto `origin https://github.com/douradonicolas2005-stack/scout.git` |

### 2.2 Fatos observados — artefatos e serviços (verificação pontual)
| Item | Evidência observada |
|---|---|
| Estrutura de topo | `backend/`, `frontend/`, `docs/`, `README.md`, `.env.example`, `.gitignore` presentes |
| Ambientes/artefatos locais | `backend/.venv` presente; `frontend/node_modules` presente; `frontend/dist` presente (`index.html`, `assets/`, `vite.svg`) |
| Documentação | 9 docs em `docs/`: `API.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `DESIGN_SYSTEM.md`, `INGESTION_ARCHITECTURE.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, `SECURITY.md`, `VISION.md`; sketch estático `docs/demo/index.html` |
| Banco local | `backend/data/scout.db` presente (gitignored por `backend/.gitignore: data/*`) |
| Storage | `backend/data/raw/.gitkeep`, `backend/data/documents/.gitkeep`; nenhum outro arquivo em `backend/data/raw/` observado |
| Segredos | nenhum `.env` real encontrado (apenas `.env.example` na raiz e backend) |
| API backend (`127.0.0.1:8000`) | não acessível no momento (`curl` falhou / sem listener) |
| Frontend dev (`5173`) | processo `node` escutando em `[::1]:5173` observado (PID reportado na verificação) |
| Ollama (`127.0.0.1:11434`) | serviço escutando em `127.0.0.1:11434` observado (PID reportado na verificação) |

### 2.3 Limitações do ambiente/execução da auditoria
- Validações dependentes de backend em execução (chamadas HTTP manuais à API local) e testes E2E/manuais de UI em navegador não foram executados.
- `pytest` não foi reexecutado nesta auditoria (ver seção 9).
- Rebuild de frontend não foi reexecutado; build pré-existente em `frontend/dist` foi inspecionado.
- `sqlite3 -readonly` refletiu PRAGMAs da sessão de leitura ad hoc (`foreign_keys=0`, `journal_mode=delete`, `busy_timeout=0`); o comportamento de runtime por conexão é definido em código (hipótese/corroboração por inspeção, ver seção 10).

---

## 3. Metodologia de auditoria (fatos observados)

- Inspeção de versionamento e árvore: `git status/log/remote/branch/ls-remote`, listagem de arquivos e diretórios.
- Inspeção de código-fonte e configuração: `backend/app/*` (API, core, db, knowledge, ingestion, intelligence, predictive, control), migração Alembic, schemas/endpoints, frontend (`src/app`, `pages`, `components`, `lib/api`, estilos/configs), testes, docs.
- Inspeção de estado de dados/migração: `alembic current/heads/history` via `backend/.venv`, consultas `sqlite3 -readonly` para tabelas/contagens e PRAGMAs.
- Verificação operacional pontual: checagem de listeners/portas e acessibilidade HTTP local.
- Validações executadas: `ruff check --no-cache app tests`, `mypy app`, `tsc -b --pretty false --incremental false`, `eslint .` (detalhes na seção 9).
- Princípio aplicado: diferenciar fatos observados de hipóteses e recomendações; registrar itens não executados/falhos.

---

## 4. Fatos observados — estrutura, backend e contratos

### 4.1 Estrutura e camadas (evidência por arquivos)
| Camada/área | Evidências (arquivos/diretórios) |
|---|---|
| Application/API | `backend/app/main.py`, `backend/app/api/router.py`, `backend/app/api/v1/endpoints/{health,system,ingestion,collection,audit}.py`, `backend/app/api/v1/schemas/*.py`, `backend/app/core/{config,logging,exceptions}.py` |
| Knowledge/DB | `backend/app/db/{base,session}.py`, `backend/app/db/migrations/env.py`, `backend/app/db/migrations/versions/426757a848bb_foundation_b_schema.py`, `backend/app/knowledge/models/domain.py`, `backend/app/knowledge/provenance.py` |
| Ingestion | `backend/app/ingestion/{bootstrap,registry,collection,scheduler}.py`, `backend/app/ingestion/connectors/{base,rss_atom}.py`, `backend/app/ingestion/pipeline/*`, `backend/app/ingestion/collectors/*` |
| Intelligence/Predictive/Control | `backend/app/intelligence/llm/{base,ollama}.py`, `backend/app/intelligence/{agents,orchestrator}/*`, `backend/app/predictive/*`, `backend/app/control/audit.py` |
| Frontend | `frontend/src/app/{App.tsx,routes.tsx,store/app-store.ts}`, `frontend/src/pages/*`, `frontend/src/components/{layout,shared,ui}/*`, `frontend/src/lib/api/{client.ts,types.ts}`, `frontend/src/styles/globals.css` |

### 4.2 Configuração e contratos (fatos observados)
- **`backend/app/core/config.py` (`class Settings`):** defaults locais `host=127.0.0.1`, `port=8000`, SQLite local, `ollama_base_url=http://127.0.0.1:11434`, `ollama_model=qwen3:4b`, `scheduler_enabled=False`, `scheduler_max_concurrent_jobs=1`, CORS local; propriedades de diretórios (`backend_dir`, `data_dir`, `raw_data_dir`, `documents_dir`, `resolved_database_url`, `cors_origins_list`).
- **`backend/app/main.py`:** lifespan com `setup_logging`, `ensure_storage_dirs`, criação/start/shutdown de scheduler (`get_scheduler/reset_scheduler`), app FastAPI com fase operacional `foundation-g` e router `/api/v1`.
- **`backend/app/api/router.py`:** inclusão de `health`, `system`, `ingestion`, `collection`, `audit`.
- **Endpoints/funções inspecionadas:**
  - `backend/app/api/v1/endpoints/health.py`: `health_check` → resposta com `phase="foundation-g"`.
  - `backend/app/api/v1/endpoints/system.py`: `system_info` (`phase="foundation-g"`, 8 módulos placeholder), `_get_alembic_revisions`, `db_status`.
  - `backend/app/api/v1/endpoints/ingestion.py`: `_record_audit`, `_connector_to_response`, `list_connectors`, `get_connector`, `create_source`, `list_sources`, `get_source`, `update_source`, `test_source_connection`.
  - `backend/app/api/v1/endpoints/collection.py`: `create_job`, `list_jobs`, `get_job`, `run_job`, `list_job_runs`, `get_run`, `list_run_events`.
  - `backend/app/api/v1/endpoints/audit.py`: `list_audit_events`.
- **Frontend integração (evidência):** `frontend/src/lib/api/client.ts` e `types.ts` implementam consumo tipado de health/system/db, conectores/fontes, teste de conexão, jobs/runs/eventos e audit-events; `DashboardPage.tsx` e `SystemPage.tsx` tratam estados loading/erro/parcial/vazio/sucesso com dados reais de API.

---

## 5. Fatos observados — banco de dados, migrações e modelo

### 5.1 Migrações e estado do banco
| Verificação | Resultado observado |
|---|---|
| `alembic current` (`backend/.venv/bin/alembic`) | `426757a848bb (head)` |
| `alembic heads` | `426757a848bb (head)` |
| `alembic history` | `<base> -> 426757a848bb (head), foundation_b_schema` |
| Tabelas (`sqlite3 -readonly backend/data/scout.db`) | `agent_runs, alembic_version, audit_events, collection_jobs, collection_runs, connectors, data_changes, documents, entities, evidence, extracted_claims, processing_events, raw_records, relationships, sources` (15 domínio + alembic) |
| Contagens (consulta direta) | `sources=0, connectors=0, collection_jobs=0, collection_runs=0, raw_records=0, documents=0, processing_events=0, data_changes=0, audit_events=0` |
| PRAGMAs (sessão `sqlite3 -readonly`) | `foreign_keys=0`, `journal_mode=delete`, `busy_timeout=0` (ver hipótese em seção 10 sobre diferença de sessão/runtime) |

### 5.2 Modelo ORM e semântica (`backend/app/knowledge/models/domain.py`, `backend/app/knowledge/provenance.py`)
- **Classes de domínio (15):** `Connector`, `Source`, `CollectionJob`, `CollectionRun`, `RawRecord`, `Document`, `ExtractedClaim`, `Evidence`, `Entity`, `Relationship`, `DataChange`, `ProcessingEvent`, `AgentRun`, `AuditEvent` (+ `TimestampMixin`).
- **Proveniência/rastreabilidade:** campos de identificação, timestamps, status, vínculos por chaves estrangeiras/referências, metadados JSON, confiança/verificação/versionamento conforme entidade (ex.: claims com tipo/confiança/verificação/versão; eventos de processamento/auditoria/alterações; jobs/runs/raw records).
- **Semântica:** enums `ClaimType` e `VerificationStatus` em `provenance.py`, incluindo distinção entre fato verificado, declaração, inferência, hipótese, previsão e desconhecido; constantes/utilidades indicam não promoção automática de inferência a fato (corroborado por teste `test_basic_read_write_and_provenance` em `tests/unit/test_db_foundation.py`, inspecionado).

---

## 6. Fatos observados — ingestão, pipeline, scheduler e conectores

### 6.1 Componentes e interfaces
- **Conectores/registro:** `backend/app/ingestion/connectors/base.py` (`BaseConnector` com `validate_config`, `check_availability`, `test_connection`, `collect`, `describe_capabilities`; `ConnectorTestResult`, `ConnectorRecord`), `backend/app/ingestion/registry.py`, `backend/app/ingestion/bootstrap.py` (sincronização idempotente de conectores built-in).
- **Conector real:** `backend/app/ingestion/connectors/rss_atom.py` (`class RssAtomConnector`, `parse_feed`, helpers) — leitura RSS/Atom, metadados/títulos/links/ids/datas, limites conservadores (máx. 5 itens, timeout/tamanho de resposta limitados), HTTP read-only.
- **Pipeline:** `backend/app/ingestion/collection.py` — funções/classes inspecionadas incluem `CollectionError`, `_record_event`, `_record_data_change`, `_record_audit`, `_source_connector_and_config`, `_should_preserve_raw`, `_content_hash`, `create_collection_job`, `_find_existing_raw`, `_persist_raw_record`, `execute_collection_job`, `get_job_runs`, `get_run_events`. Fluxo observável: criação/execução de job/run, coleta via conector, normalização/validação/deduplicação básica, persistência condicional de raw, registro de eventos/alterações e atualização de estados/`last_collected_at`.
- **Scheduler:** `backend/app/ingestion/scheduler.py` (`class IngestionScheduler`, `get_scheduler`, `reset_scheduler`) — APScheduler Background, estado canônico no banco, dispatch controlado por tick, reidratação quando habilitado, desabilitado por padrão e sem paralelismo pesado (`max_concurrent_jobs` efetivo mínimo 1).

### 6.2 Decisão 4 (estado observado)
- **Recurso de referência:** `https://www.w3.org/news/feed/` (W3C News, RSS público), conector `rss_atom`.
- **Status:** **confirmado e autorizado** pelo usuário para continuidade em testes/leitura/coleta real local de referência, com restrições: read-only, metadados/títulos/links/ids/datas, máx. 5 itens, timeouts e limites de tamanho/resposta; sem preservação de corpo/conteúdo completo no pipeline padrão (preservação condicional apenas se explicitamente permitida).
- **Evidências de registro:** `README.md`, `docs/PROJECT_STATUS.md`, `docs/ARCHITECTURE.md`, `docs/INGESTION_ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/SECURITY.md` e comentários em `backend/tests/unit/test_ingestion_registry.py` e `backend/tests/unit/test_collection_pipeline.py` (commit `afd481e`).
- **Uso em testes (inspecionado):** constante `W3C_NEWS_FEED_URL` e testes que realizam acesso HTTP real de leitura ao feed (ex.: `test_source_test_connection_real_feed` em `test_ingestion_registry.py`; `test_create_and_run_collection_job_real_pipeline`, `test_pipeline_deduplicates_on_second_run`, `test_scheduler_dispatches_pending_job_from_db` em `test_collection_pipeline.py`).

---

## 7. Fatos observados — frontend, UX e integração

- **Navegação/rotas (`frontend/src/app/routes.tsx`, `App.tsx`):** 8 áreas definidas (`/radar`, `/dossiers`, `/knowledge-graph`, `/predictions`, `/scenario-lab`, `/action-center`, `/agent-control`, `/system`, todas com `implemented: false` na definição de navegação) + rota Foundation/Dashboard.
- **Placeholders não simulados:** páginas `RadarPage`, `DossiersPage`, `KnowledgeGraphPage`, `PredictionsPage`, `ScenarioLabPage`, `ActionCenterPage`, `AgentControlPage` utilizam `ModulePlaceholder` (`frontend/src/pages/ModulePlaceholder.tsx`) com mensagem explícita de módulo não implementado e sem simulação de dados/conexões/processamento.
- **Integração real:** `DashboardPage.tsx` consulta `health/system/info/db/status`; `SystemPage.tsx` consome e exibe conectores, fontes, jobs, runs, eventos e auditoria, com ações suportadas (testar conexão, criar/executar job, inspecionar histórico) e estados de UI (`PageState`, `PageHeader`, componentes em `frontend/src/components/*`).
- **Design System/UX:** tokens SCOUT e temas claro/escuro (`frontend/src/styles/globals.css`, `index.html` anti-flash, store), App Shell responsivo com sidebar/header/breadcrumbs, busca global desabilitada (`GlobalSearch.tsx`), acessibilidade básica (skip link, foco, labels/aria nos componentes inspecionados).
- **Contratos tipados:** `frontend/src/lib/api/client.ts` e `frontend/src/lib/api/types.ts` alinham-se aos endpoints/`phase=foundation-g` inspecionados.

---

## 8. Fatos observados — segurança, controle e consistência documental

### 8.1 Segurança e controles
- **Superfície:** binding/uso local loopback previsto (`127.0.0.1`), CORS local; sem exposição remota no desenho.
- **Segredos/dados:** `.env` não versionado; referências de autenticação em fonte (`auth_method`, `auth_credential_ref`); dados/storage locais gitignored.
- **Confiança:** conteúdo externo tratado como dado não confiável (conectores/pipeline), validações de config/entradas/saídas, limites/timeouts/tamanho, preservação condicional de raw.
- **Rastreabilidade:** `audit_events`, `processing_events`, `data_changes`, jobs/runs/raw records.
- **IA local:** abstração Ollama com verificação sob demanda, sem inferência automática (`intelligence/llm/base.py`, `ollama.py`, config/schemas).
- **Controle operacional:** scheduler conservador DB-canônico, desabilitado por padrão, sem paralelismo pesado.

### 8.2 Consistência documentação–código
- **Alinhado (observado):** `phase=foundation-g` (health/system/types), migração `426757a848bb`, 8 módulos placeholder, scheduler default off, modo Ollama sob demanda, conector `rss_atom` e pipeline rastreável mínimo, Decisão 4 confirmada.
- **Limitações/estado real refletidos em docs:** ausência de E2E/UI automatizado, escopo funcional restrito, dependência de rede externa em testes para o recurso confirmado, áreas de produto como placeholders.

---

## 9. Validações e testes — resultados e evidências

### 9.1 Validações executadas nesta auditoria
| Área | Comando | Resultado |
|---|---|---|
| Backend lint | `cd backend && .venv/bin/ruff check --no-cache app tests` | **OK** — `All checks passed!` (exit 0) |
| Backend tipagem | `cd backend && .venv/bin/mypy --cache-dir /tmp/opencode-scout-mypy-cache app` | **OK** — `Success: no issues found in 53 source files` (exit 0) |
| Frontend tipagem | `cd frontend && ./node_modules/.bin/tsc -b --pretty false --incremental false` | **OK** (exit 0) |
| Frontend lint | `cd frontend && ./node_modules/.bin/eslint .` | **OK** (exit 0) |
| Frontend build (artefato) | inspeção de `frontend/dist/` | **OK (artefato presente e inspecionado)**; rebuild não reexecutado |

> Observação: uma invocação inicial de ruff com flag inválida (`--no-cache=1`) retornou erro de uso (exit 2); a execução correta com `--no-cache` passou. Não houve falha de lint/tipagem no código.

### 9.2 Suíte de testes backend (inspecionada; não reexecutada integralmente nesta auditoria)
| Arquivo | Escopo/funções representativas inspecionadas |
|---|---|
| `backend/tests/unit/test_health.py` | `test_health_returns_ok` (espera `status=ok`, `phase=foundation-g`) |
| `backend/tests/unit/test_config.py` | `test_defaults_bind_loopback`, `test_ollama_defaults_local`, `test_scheduler_disabled_by_default`, `test_storage_paths_defined` |
| `backend/tests/unit/test_db_foundation.py` | `test_alembic_migration_creates_all_tables`, `test_basic_read_write_and_provenance` (inclui semântica de claim não promovida a fato) |
| `backend/tests/unit/test_system_endpoints.py` | `test_system_info_returns_modules_and_metadata`, `test_db_status_reports_migrated_schema` |
| `backend/tests/unit/test_ingestion_registry.py` | `test_parse_feed_rss_metadata_only`, `test_connectors_list_and_get`, `test_source_crud_and_activation`, `test_source_validation_rejects_unknown_connector`, `test_source_test_connection_real_feed` (HTTP real ao feed W3C confirmado) |
| `backend/tests/unit/test_collection_pipeline.py` | `test_create_and_run_collection_job_real_pipeline`, `test_pipeline_deduplicates_on_second_run`, `test_job_not_executed_when_execute_now_false`, `test_scheduler_dispatches_pending_job_from_db` (leituras HTTP reais ao feed W3C confirmado em cenários de coleta) |

- **Resultado documentado na validação final da Subetapa H (`docs/PROJECT_STATUS.md`):** `pytest -q` → **18 passed** (0.93s), com expectativas alinhadas a `phase=foundation-g` e schema `426757a848bb`.
- **Execução nesta auditoria:** **não reexecutada** (item não executado, ver 9.3).

### 9.3 Testes/validações que falharam ou não puderam ser executados
| Item | Status | Justificativa/evidência |
|---|---|---|
| `pytest -q` (suíte backend completa) | **Não executado nesta auditoria** | Suíte inclui leituras HTTP reais externas ao recurso da Decisão 4 confirmado (`https://www.w3.org/news/feed/`), conforme inspeção dos testes e documentação; não reexecutado para evitar acesso externo adicional e consumo desnecessário, em conformidade com restrições conservadoras da auditoria. Resultado prévio documentado: 18 passed (Subetapa H). |
| Rebuild frontend (`npm run build`) | **Não reexecutado** | Artefato `frontend/dist` presente e inspecionado; rebuild omitido para evitar escrita desnecessária. Typecheck/lint executados com sucesso. |
| Testes E2E/manuais de UI em navegador | **Não executados / não disponíveis como suíte automatizada** | Não há suíte E2E automatizada identificada no repositório; verificação manual interativa não realizada nesta sessão. |
| Chamadas funcionais à API local em runtime (`/api/v1/*`) | **Não executadas** | Backend não acessível em `127.0.0.1:8000` no momento da verificação; validação baseada em inspeção de código/contratos e resultados documentados/prévios. |
| Testes de lint/tipagem executados | **Nenhuma falha** | ruff, mypy, tsc e eslint concluídos com sucesso. |

---

## 10. Hipóteses (explicitamente separadas dos fatos)

1. **PRAGMAs SQLite observados via sessão `sqlite3 -readonly` vs runtime:** a sessão ad hoc reportou `foreign_keys=0`, `journal_mode=delete`, `busy_timeout=0`, enquanto `backend/app/db/session.py` configura `foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000` em eventos de conexão. **Hipótese:** a diferença decorre do escopo por conexão/sessão do `sqlite3` e do modo de abertura usado na inspeção, não de ausência de configuração no runtime da aplicação. **Base:** inspeção de código; não houve validação com API em execução nesta auditoria.
2. **Operação ponta-a-ponta em runtime local:** dada a consistência de contratos/código, artefatos (`.venv`, `dist`, DB migrada) e validações anteriores documentadas, **hipótese** de que os fluxos inspecionados operam conforme implementado quando o backend é iniciado corretamente; confirmação dinâmica completa não foi realizada nesta sessão.
3. **Impacto prático da dependência externa dos testes:** **hipótese** de risco de instabilidade/flakiness em ambientes sem rede ou com indisponibilidade do feed W3C, apesar de o recurso estar confirmado e dos limites conservadores; mitigação dependeria de segregação/mocks (recomendação).

---

## 11. Recomendações (condicionadas a autorização explícita)

1. **Testes offline/determinísticos:** segregar testes que dependem de rede externa (ex.: marcar como integração externa/opt-in) e prover suíte padrão com fixtures/mocks para parsing e pipeline, mantendo validação real ao feed confirmado como teste opcional controlado.
2. **Cobertura E2E mínima:** introduzir testes automatizados de fluxos críticos (System/Source Manager: teste de conexão, criação/execução/inspeção de job/run/eventos, leitura de auditoria) para reduzir risco de regressão de UI/integração.
3. **Clareza semântica de status de módulos:** revisar a sinalização de `system` em `frontend/src/app/routes.tsx`/metadados para distinguir “monitoramento operacional mínimo implementado” de “módulo de domínio completo não implementado”, mantendo coerência com `/api/v1/system/info`.
4. **Padronização de ambiente:** considerar atualização/definição de versão suportada de Python (atualmente 3.9.6, funcional porém EOL upstream) e política de atualização/auditoria de dependências em etapa dedicada.
5. **Evolução pós-Foundation:** somente com autorização de escopo, avançar para correções planejadas ou novos domínios (ex.: Dossiers), com migrações/contratos/testes e controles de rastreabilidade/segurança alinhados ao desenho local-first.

---

## 12. Conclusão e classificação

### 12.1 Síntese dos achados
- **Conformidades observadas:** base local-first e modular implementada; contratos de sistema/saúde/DB e ingestão/monitoramento presentes; migração `426757a848bb` em head com 15 entidades de domínio e mecanismos de proveniência/rastreabilidade; scheduler conservador DB-canônico desabilitado por padrão; abstração Ollama sob demanda sem inferência automática; frontend com integração real para estado/monitoramento mínimo e placeholders explícitos sem simulação para módulos de domínio; validações estáticas (ruff, mypy, tsc, eslint) aprovadas; documentação consistente com o estado inspecionado.
- **Ressalvas:** `pytest` não reexecutado nesta auditoria (suíte com dependência de HTTP externo ao recurso confirmado, 18 passed documentados em H), ausência de E2E/UI automatizado, escopo funcional limitado à Foundation e estado operacional local sem backend ativo/DB vazia no momento da verificação.

### 12.2 Classificação
**APROVADA COM RESSALVAS.**

A Foundation V1.1 (A–H) é considerada tecnicamente consistente e verificável dentro do escopo definido e das evidências coletadas, com ressalvas de cobertura de testes dinâmicos/E2E e de alcance funcional que devem ser tratadas ou explicitamente aceitas antes de expansões de escopo.

---

## 13. Apêndice — evidências de referência rápida

- **Versionamento:** `300f2bc`, `631c77d`, `afd481e` (`git log --oneline`).
- **Migração:** `backend/app/db/migrations/versions/426757a848bb_foundation_b_schema.py`.
- **Modelo:** `backend/app/knowledge/models/domain.py` (classes `Connector`, `Source`, `CollectionJob`, `CollectionRun`, `RawRecord`, `Document`, `ExtractedClaim`, `Evidence`, `Entity`, `Relationship`, `DataChange`, `ProcessingEvent`, `AgentRun`, `AuditEvent`); `backend/app/knowledge/provenance.py`.
- **Ingestão/pipeline/scheduler:** `backend/app/ingestion/collection.py` (`create_collection_job`, `execute_collection_job`, `get_job_runs`, `get_run_events`, `_should_preserve_raw`, `_record_event/_data_change/_audit`), `backend/app/ingestion/scheduler.py` (`IngestionScheduler`), `backend/app/ingestion/connectors/rss_atom.py` (`RssAtomConnector`, `parse_feed`), `backend/app/ingestion/connectors/base.py`.
- **API:** `backend/app/api/v1/endpoints/{health,system,ingestion,collection,audit}.py`, `backend/app/api/router.py`.
- **Frontend:** `frontend/src/pages/{DashboardPage,SystemPage,ModulePlaceholder,ActionCenterPage,AgentControlPage,DossiersPage,KnowledgeGraphPage,PredictionsPage,RadarPage,ScenarioLabPage}.tsx`, `frontend/src/lib/api/{client.ts,types.ts}`, `frontend/src/app/{App.tsx,routes.tsx,store/app-store.ts}`.
- **Testes:** `backend/tests/unit/{test_health.py,test_config.py,test_db_foundation.py,test_system_endpoints.py,test_ingestion_registry.py,test_collection_pipeline.py}`.
- **Docs:** `README.md`, `docs/{API,ARCHITECTURE,DATA_MODEL,DESIGN_SYSTEM,INGESTION_ARCHITECTURE,PROJECT_STATUS,ROADMAP,SECURITY,VISION}.md`.
