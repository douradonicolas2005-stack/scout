# Relatório de Estabilização Pós-Auditoria — SCOUT Foundation V1.1

- **Data de execução:** 2026-11-19
- **Relatório de auditoria de referência:** `docs/audits/FOUNDATION_V1.1_AUDIT.md` (classificação: **APROVADA COM RESSALVAS**, commit-base `afd481e` / estado pós-auditoria `865018a`)
- **Repositório/branch:** `douradonicolas2005-stack/scout` — `main` em `865018a` (`docs: add Foundation V1.1 audit report`), rastreando `origin/main`, working tree limpo antes da criação deste relatório
- **Diretório:** `/Users/nicolasdrumonddourado/Documents/Default Project/scout`
- **Escopo desta etapa:** verificação e estabilização da Foundation V1.1 (testes backend, API, integração frontend-backend, Dashboard/System, integridade do SQLite, estado Alembic, segurança/execução local, compatibilidade Python, documentação técnica) e emissão de parecer de aceite. **Módulo Dossiers não desenvolvido.**

> **Restrições observadas:** sem reconstrução/refatoração/novas funcionalidades, sem alterações de modelo/migrações destrutivas, sem instalação de dependências, sem commits/push, sem ativação automática do scheduler, sem coletas externas automáticas, sem agentes paralelos, sem APIs pagas/recursos corporativos, sem modificação de arquivos antes do plano de correções exceto este relatório (única alteração autorizada). Execuções temporárias controladas em `127.0.0.1` encerradas ao final.

---

## 1. Resumo executivo

A Foundation V1.1 permanece funcional e consistente no escopo A–H. As validações estáticas e a suíte automatizada do backend foram reexecutadas com sucesso (ruff, mypy, pytest 18/18). A API FastAPI foi iniciada temporariamente em `127.0.0.1:8765` e os principais endpoints de sistema/ingestão/monitoramento responderam conforme contrato, com banco conectado, migração em head e PRAGMAs de runtime ativos. O frontend passou em typecheck, lint e build de produção; por inspeção de código, Dashboard e System consomem dados reais da API com tratamento de estados e sem simulação de domínio. O banco SQLite local está íntegro, com schema/índices/FKs presentes e Alembic consistente (sem pendências). Persistem ressalvas conhecidas e não bloqueantes para aceite da Foundation: dependência de leituras HTTP externas reais na suíte de testes (recurso W3C confirmado), ausência de testes E2E/UI automatizados e inspeção visual de navegador nesta etapa, Python 3.9.6 (EOL upstream) e margem de memória limitada em 8 GB para execução simultânea completa com Ollama.

**Parecer desta etapa:** **APROVADA COM RESSALVAS** (infraestrutura essencial estável para evolução controlada; ver plano de correções e respostas finais).

---

## 2. Ambiente utilizado

### 2.1 Hardware/SO e runtime (fatos observados)
| Item | Evidência |
|---|---|
| SO / arquitetura | macOS 15.7.3, `arm64` (`sw_vers -productVersion`, `uname -m`) |
| Memória declarada (contexto) | MacBook Air Apple Silicon, 8 GB RAM |
| Python (venv backend) | `Python 3.9.6` (`backend/.venv/bin/python --version`) |
| Node.js / npm | `v26.5.0` / `11.17.0` (`node --version`, `npm --version`) |
| Git | `main...origin/main`, HEAD `865018a`, limpo antes deste relatório (`git status -sb`, `git log`) |
| Banco local | `backend/data/scout.db` (304 KB; gitignored; único arquivo de dados versionado em `backend/data/`: `.gitkeep`) |

### 2.2 Artefatos e estado operacional observado
| Item | Evidência |
|---|---|
| Artefatos locais | `backend/.venv`, `frontend/node_modules`, `frontend/dist` presentes |
| Documentação | `docs/` com 9 docs + `docs/demo/` + `docs/audits/FOUNDATION_V1.1_AUDIT.md` |
| `.env` reais | não encontrados (apenas `.env.example` na raiz e em `backend/`, `frontend/`) |
| Serviços no momento da verificação inicial | backend `127.0.0.1:8000` inacessível; frontend dev listener observado em `5173`; Ollama listener em `127.0.0.1:11434` (verificação pontual) |
| Validações temporárias desta etapa | API iniciada em `127.0.0.1:8765` (uvicorn, PID efêmero) e **encerrada** após testes; build frontend gerado em diretório temporário `/tmp/scout-frontend-build-audit` |

### 2.3 Limitações desta execução
- **Sem teste E2E/UI automatizado** e **sem inspeção visual em navegador** (avaliação de Dashboard/System por inspeção de código e build/type/lint).
- **`pytest` reexecutado** com sucesso, mas a suíte inclui **leituras HTTP reais externas** ao feed W3C confirmado (dependência de rede); validação não é totalmente offline.
- **`/api/v1/system/info` e `/db/status`** acessíveis localmente (documentados em API); `/docs` e `/openapi.json` expostos pelo FastAPI quando ativo (superfície local padrão, não validada por navegação, mas inferida por config/código).
- **Sem `pytest-cov`** configurado/instalado (`--cov` não reconhecido); cobertura não disponível.
- **Efeito colateral observado e controlado:** ao acessar endpoints de conectores durante a validação temporária, ocorreu sincronização idempotente de metadados do conector built-in no banco real (`connectors` passou a conter `rss_atom` registrado; confirmado por leitura posterior). Nenhuma fonte, job, run, evento de processamento ou auditoria foi criado. Estado WAL (`.db-shm/.db-wal`) observado, compatível com operação SQLite WAL.

---

## 3. Etapa A — Revisão das ressalvas anteriores (lista de verificação)

Fonte: `docs/audits/FOUNDATION_V1.1_AUDIT.md` (seções 9.3, 10, 11, 12) e `docs/PROJECT_STATUS.md`.

| # | Problema/ressalva identificada | Evidência original | Situação atual (revalidada) | Procedimento de validação executado | Critério de aprovação | Status |
|---|---|---|---|---|---|---|
| A1 | Suíte backend não reexecutada na auditoria; dependência de HTTP externo real (Decisão 4/W3C) | Audit §9.3, §11; testes `test_source_test_connection_real_feed`, `test_create_and_run_collection_job_real_pipeline`, `test_pipeline_deduplicates_on_second_run`, `test_scheduler_dispatches_pending_job_from_db` | **Decisão 4 confirmada** (docs/código em `865018a`). `pytest -v` reexecutado: **18 passed, 0 failed, 0 skipped** (1.15s). Dependência externa permanece por desenho da suíte. | `cd backend && .venv/bin/python -m pytest -v` | Suíte verde sem falhas; dependência externa conhecida e documentada | **Atendido com ressalva** (não offline) |
| A2 | Ausência de testes E2E/UI automatizados e inspeção manual de navegador | Audit §9.3, §12 | Sem suíte E2E identificada; não executada inspeção visual. Typecheck/lint/build frontend **OK**; integração real verificada por inspeção de `DashboardPage.tsx`, `SystemPage.tsx`, `client.ts`, `types.ts`. | `npm run typecheck`, `npm run lint`, `npx vite build` + inspeção de código | Fluxos críticos de UI cobertos por validação automatizada e/ou inspeção | **Ressalva mantida** |
| A3 | Build frontend não reexecutado na auditoria (apenas `dist` inspecionado) | Audit §9.1 | Build de produção reexecutado com sucesso (1627 módulos, saída temporária). | `npx vite build --outDir /tmp/scout-frontend-build-audit` | Build concluído sem erro | **Atendido** |
| A4 | Backend/API não ativo e DB sem registros operacionais no momento da auditoria | Audit §2.2, §12 | Backend iniciou em `127.0.0.1:8765`, endpoints responderam corretamente; DB íntegro e migrado (contagens de domínio 0 antes/compatível; sincronização de conector builtin observada). | Inicialização uvicorn temporária + `curl` em endpoints + queries SQLite + encerramento do processo | API operável localmente, DB íntegro/migrado | **Atendido** |
| A5 | PRAGMAs SQLite ad hoc (`foreign_keys=0/journal_mode=delete`) vs runtime esperado | Audit §2.3, §10 | **Confirmado em runtime:** `/api/v1/db/status` reportou `foreign_keys=1`, `journal_mode="wal"`, `busy_timeout=5000`. Código aplica PRAGMAs em `backend/app/db/session.py:set_sqlite_pragma`. Sessão `sqlite3 -readonly` isolada ainda reporta defaults da sessão (não do runtime). | Inspeção `session.py`; consulta `GET /db/status`; `PRAGMA` via `sqlite3 -readonly` (comparativo) | Runtime com `foreign_keys=ON`, `WAL`, `busy_timeout` ativo | **Atendido** |
| A6 | Status semântico ambíguo de `system` (`implemented:false` em rotas/metadados) vs monitoramento real na UI | Audit §8.2, recomendação | Inalterado: `frontend/src/app/routes.tsx` (`NAV_ITEMS`) marca `system` como `implemented:false`; `system/info` lista módulos como placeholders; `SystemPage` fornece monitoramento/controles mínimos reais. | Inspeção de `routes.tsx`, `system.py`, `SystemPage.tsx` | Sem ambiguidade funcional/documental | **Ressalva menor mantida** (não bloqueante) |
| A7 | Python 3.9.6 (EOL upstream) / atualização de dependências | Audit §11, recomendação | Ambiente atual funcional (testes/lint/mypy/build ok, dependências pinadas). Sem atualização realizada (não autorizada). | Verificação de versões, execução de suíte e validações | Ambiente suportado e estável para Foundation | **Atendido com ressalva** (risco de manutenção futura) |
| A8 | Consumo/memória em 8 GB com backend+frontend+Ollama | Audit §11, recomendação | Não executado teste de estresse (proibido). Design conservador observado (`scheduler_enabled=False`, `max_concurrent_jobs=1`, sem paralelismo pesado). Listener Ollama observado em `127.0.0.1:11434`. | Inspeção de config/código e estado de portas | Operação viável sem reconstrução infra | **Ressalva condicional** (operacional, não validada sob carga) |

---

## 4. Etapa B — Testes do backend

### 4.1 Comandos executados (não destrutivos)
- `cd backend && .venv/bin/ruff check --no-cache app tests` → **EXIT 0**, `All checks passed!`
- `cd backend && .venv/bin/mypy --cache-dir /private/var/folders/.../opencode/scout-mypy-cache app` → **EXIT 0**, `Success: no issues found in 53 source files`
- `cd backend && .venv/bin/python -m pytest -v` → **EXIT 0**, **18 passed in 1.15s**
- `cd backend && .venv/bin/python -m pytest --cov` → **falha de argumento** (`unrecognized arguments: --cov`, plugin não disponível); **cobertura não configurada**

### 4.2 Resultado detalhado (pytest)
| Métrica | Valor |
|---|---|
| Coletados | 18 |
| Aprovados | 18 |
| Reprovados | 0 |
| Ignorados/skipped | 0 |
| Erros de configuração | 0 |
| Falhas de integração observadas | 0 |

| Arquivo | Testes | Resultado |
|---|---|---|
| `tests/unit/test_collection_pipeline.py` | `test_create_and_run_collection_job_real_pipeline`, `test_pipeline_deduplicates_on_second_run`, `test_job_not_executed_when_execute_now_false`, `test_scheduler_dispatches_pending_job_from_db` | 4 PASSED |
| `tests/unit/test_config.py` | `test_defaults_bind_loopback`, `test_ollama_defaults_local`, `test_scheduler_disabled_by_default`, `test_storage_paths_defined` | 4 PASSED |
| `tests/unit/test_db_foundation.py` | `test_alembic_migration_creates_all_tables`, `test_basic_read_write_and_provenance` | 2 PASSED |
| `tests/unit/test_health.py` | `test_health_returns_ok` | 1 PASSED |
| `tests/unit/test_ingestion_registry.py` | `test_parse_feed_rss_metadata_only`, `test_connectors_list_and_get`, `test_source_crud_and_activation`, `test_source_validation_rejects_unknown_connector`, `test_source_test_connection_real_feed` | 5 PASSED |
| `tests/unit/test_system_endpoints.py` | `test_system_info_returns_modules_and_metadata`, `test_db_status_reports_migrated_schema` | 2 PASSED |

### 4.3 Isolamento de dados e dependências (fatos observados)
- **Banco:** testes inspecionados (`test_ingestion_registry.py`, `test_collection_pipeline.py`, `test_db_foundation.py`) criam bancos temporários em `tmp_path` e executam `alembic upgrade` sobre DB efêmero; overrides de dependência FastAPI usados. **Não foi observada execução destrutiva sobre `backend/data/scout.db`.**
- **Rede externa:** testes que usam `W3C_NEWS_FEED_URL = "https://www.w3.org/news/feed/"` realizam leituras HTTP reais (metadados/títulos, máx. 5 itens, limites conservadores), conforme Decisão 4 confirmada. Execução desta etapa obteve sucesso, mas depende de disponibilidade/rede externa.
- **Cobertura:** ferramenta não presente/configurada no ambiente.

---

## 5. Etapa C — Validação da API

### 5.1 Inicialização temporária controlada
- **Comando:** `uvicorn app.main:app --host 127.0.0.1 --port 8765` (processo em background temporário)
- **Bind:** `127.0.0.1` (conforme exigido; `0.0.0.0` não utilizado)
- **Resultado:** aplicação iniciou e respondeu; processo **encerrado** após validação (`kill` + confirmação de ausência de listener em `8765`).
- **Lifespan/integração observados por código:** `app/main.py` executa `setup_logging`, `ensure_storage_dirs`, inicializa scheduler conforme config (disabled por padrão) e registra `api_router` em `/api/v1`; CORS via `settings.cors_origin_list`.

### 5.2 Endpoints validados (somente leitura/consultas seguras)

| Rota | Método | Código | Resultado observado | Erros/eventos |
|---|---:|---:|---|---|
| `/api/v1/health` | GET | 200 | `status=ok`, `service=SCOUT API`, `version=0.1.0-foundation-v1.1`, `environment=development`, `phase=foundation-g`, timestamp presente | — |
| `/api/v1/system/info` | GET | 200 | `phase=foundation-g`, `database=sqlite`, `ollama` (`base_url`, `model=qwen3:4b`, `mode=abstraction-availability-only`), `scheduler` (`enabled=false`, `max_concurrent_jobs=1`, `state=db-canonical-ready`), 8 módulos `placeholder`/`implemented=false` | — |
| `/api/v1/db/status` | GET | 200 | `connected=true`, `dialect=sqlite`, 15 tabelas + contagens, `alembic_revision=426757a848bb`, `alembic_revisions=["426757a848bb"]`, `foreign_keys=1`, `journal_mode=wal`, `busy_timeout=5000`, `error=null` | — |
| `/api/v1/ingestion/connectors` | GET | 200 | 1 item: `rss_atom` (`RSS/Atom Feed`, `status=registered`, capabilities/config_schema compatíveis com limites: `max_items_hard_limit=5`, metadata_only) | — |
| `/api/v1/ingestion/connectors/rss_atom` | GET | 200 | Mesmo registro do conector por chave | — |
| `/api/v1/ingestion/sources` | GET | 200 | `{"items":[]}` | — |
| `/api/v1/ingestion/jobs` | GET | 200 | `{"items":[]}` | — |
| `/api/v1/system/audit-events` | GET | 200 | `{"items":[]}` | — |
| `/api/v1/ingestion/jobs/nonexistent` | GET | 404 | `{"detail":"Job not found"}` (tratamento de recurso inexistente) | esperado |

### 5.3 Verificações complementares (código/observação)
- **SQLite/SQLAlchemy:** sessão via `get_db`/`SessionLocal` (`app/db/session.py`), PRAGMAs aplicados por conexão; conectividade confirmada por `/db/status`.
- **Validação de dados/exceções:** schemas Pydantic e handlers FastAPI presentes (inspeção de endpoints/schemas); resposta 404 estruturada observada.
- **Operações mutáveis:** **não executadas** (`POST` de criação/teste/execução, `PATCH/PUT/DELETE`) durante esta validação. Apenas GETs.
- **Efeito colateral observado:** leitura do banco real após validação mostrou inserção/sincronização idempotente do conector builtin `rss_atom` (`status=registered`, timestamp de criação correspondente à janela de execução). A implementação realiza `sync_builtin_connectors_to_db` em endpoints de listagem/consulta de conectores (`backend/app/api/v1/endpoints/ingestion.py`), o que explica mutação de metadados de conector em operação de leitura (limitada e idempotente).

---

## 6. Etapa D — Integridade do banco de dados (modo leitura)

### 6.1 Integridade e PRAGMAs
| Verificação | Resultado |
|---|---|
| `PRAGMA integrity_check;` (`sqlite3 -readonly`) | `ok` |
| `PRAGMA foreign_key_check;` (`sqlite3 -readonly`) | sem linhas (sem violações) |
| PRAGMAs (sessão `sqlite3 -readonly`) | `foreign_keys=0`, `journal_mode=delete`, `busy_timeout=0` (sessão ad hoc) |
| PRAGMAs efetivos em runtime | `foreign_keys=1`, `journal_mode=wal`, `busy_timeout=5000` (via `GET /db/status` e `app/db/session.py`) |
| Arquivos WAL | `scout.db-wal` e `scout.db-shm` presentes (compatível com modo WAL) |

### 6.2 Estrutura, tabelas, índices e relacionamentos (fatos observados)
- **Tabelas:** 15 de domínio + `alembic_version` (`agent_runs`, `audit_events`, `collection_jobs`, `collection_runs`, `connectors`, `data_changes`, `documents`, `entities`, `evidence`, `extracted_claims`, `processing_events`, `raw_records`, `relationships`, `sources`).
- **Contagens (domínio, pré-existentes):** 0 em fontes/jobs/runs/raw/documents/eventos/alterações/auditoria; `alembic_version=1`; `connectors=1` após sincronização idempotente observada na Etapa C.
- **Índices:** presentes conforme migração (únicos/funcionais em chaves e campos de consulta, ex.: `ix_connectors_key` único, índices em status/source/job/run/datas/hashes/relacionamentos).
- **Foreign keys:** declaradas e coerentes entre entidades de ingestão/rastreabilidade/conhecimento (ex.: `collection_jobs.source_id -> sources.id`, `collection_runs -> jobs/sources`, `raw_records -> sources/runs`, `documents -> sources/raw_records`, `extracted_claims/evidence/relationships/entities` encadeados, `processing_events/data_changes` vinculados quando aplicável).
- **Modelo (inspeção):** `backend/app/knowledge/models/domain.py` define as 15 classes de domínio; `backend/app/knowledge/provenance.py` define semântica de claims/verificação.

### 6.3 Alembic
| Verificação (`backend/.venv/bin/alembic`) | Resultado |
|---|---|
| `current` | `426757a848bb (head)` |
| `heads` | `426757a848bb (head)` |
| `history` | `<base> -> 426757a848bb (head), foundation_b_schema` |
| `branches` | (nenhuma) |
| Migrações pendentes/divergências | **não identificadas**; versão registrada corresponde à migração disponível |

**Nenhuma migração executada. Nenhuma tabela/registro alterado manualmente.**

---

## 7. Etapa E — Validação do frontend

### 7.1 Execuções
| Verificação | Comando | Resultado |
|---|---|---|
| TypeScript typecheck | `npm run typecheck` (`tsc -b --pretty false`) | **OK** (exit 0) |
| ESLint | `npm run lint` (`eslint .`) | **OK** (exit 0) |
| Build de produção | `npx vite build --outDir /tmp/scout-frontend-build-audit` | **OK** (exit 0), `✓ 1627 modules transformed`, artefatos `index.html`, `assets/index-*.css/js` gerados |

### 7.2 Inspeção de configuração e integração (fatos observados)
| Item | Evidência |
|---|---|
| Vite/dev server | `frontend/vite.config.ts`: `host 127.0.0.1`, `port 5173`, proxy `/api -> http://127.0.0.1:8000`, preview `127.0.0.1:4173` |
| Variáveis de ambiente | `frontend/.env.example`: `VITE_API_BASE_URL=http://127.0.0.1:8000`, `VITE_APP_PHASE=00-foundation-v1.1`; sem `.env` real no frontend |
| Cliente API | `frontend/src/lib/api/client.ts`: `BASE_URL` de `VITE_API_BASE_URL` (fallback vazio), tratamento de erros (`detail` string/array), métodos para `health/systemInfo/dbStatus`, conectores/fontes, teste de conexão, jobs/runs/eventos, auditoria |
| Tipos/contratos | `frontend/src/lib/api/types.ts` alinhado a `phase=foundation-g` e respostas inspecionadas |
| Estado/tema | `frontend/src/app/store/app-store.ts` (Zustand, tema claro/escuro com persistência) |
| Rotas/shell | `frontend/src/app/routes.tsx`, `App.tsx`, layout compartilhado (`components/layout`, `components/shared`) |

### 7.3 Dashboard e System (inspeção funcional de código)
| Área | Evidências | Avaliação |
|---|---|---|
| **Dashboard** (`frontend/src/pages/DashboardPage.tsx`) | Consulta `api.health()` e `Promise.allSettled([api.systemInfo(), api.dbStatus()])`; estados `loading/error/ready` com tratamento parcial (`systemError/dbError`); exibe dados reais (status, versão, fase, módulos, DB/tabelas/revisão/journal); mensagens explícitas de indisponibilidade/erro sem inventar dados | **Integração real, sem simulação de dados de domínio** |
| **System** (`frontend/src/pages/SystemPage.tsx`) | Carrega `system/info`, `db/status`, conectores, fontes, jobs, runs, eventos e `audit-events`; ações reais suportadas (`testSourceConnection`, `createJob`, `runJob`, seleção/inspeção de runs/eventos); estados de carregamento/erro/vazio/sucesso, badges de status, formatação de datas/IDs | **Monitoramento e controles mínimos reais**, escopo de plataforma/ingestão |
| **Módulos de produto** | `Radar/Dossiers/KnowledgeGraph/Predictions/ScenarioLab/ActionCenter/AgentControl` usam `ModulePlaceholder` (`frontend/src/pages/ModulePlaceholder.tsx`) com texto explícito de não implementação e sem simulação | **Conforme Foundation** |

### 7.4 Observações
- **Problema funcional identificado (baixo/semântico):** `routes.tsx` define `implemented:false` para todas as 8 áreas de navegação (inclui `system`), enquanto a página System entrega monitoramento/controles reais de infraestrutura/ingestão. Não impede uso nem simula funcionalidade de domínio; pode gerar ambiguidade documental/UX.
- **Inspeção visual em navegador:** não realizada nesta etapa (limitação registrada).

---

## 8. Etapa F — Segurança e execução local

| Controle | Evidência | Resultado |
|---|---|---|
| Backend em loopback | `backend/app/core/config.py`: `host="127.0.0.1"`; `uvicorn` executado com `--host 127.0.0.1`; nenhuma ocorrência de `0.0.0.0` no código-fonte/config do projeto (ocorrências apenas em dependências de `backend/.venv`) | **OK** |
| Exposição remota desnecessária | Design local-first; docs/openapi padrão FastAPI disponíveis quando serviço ativo (uso local). Sem configuração de bind externo no projeto | **OK (contexto local)** |
| Credenciais em código-fonte | Busca por segredos/tracking não indica credenciais versionadas; `.env` ausentes e gitignored (`.gitignore`, `backend/.gitignore`) | **OK** |
| CORS | `cors_origins="http://127.0.0.1:5173,http://localhost:5173"`; middleware `allow_origins=settings.cors_origin_list`, métodos/headers amplos em contexto local | **OK** para escopo local |
| `.gitignore` e dados | Raiz/backend/frontend ignoram `__pycache__`, venv, caches, `node_modules`, `dist` frontend, `backend/data/*` (exceto `.gitkeep`), `.db/.sqlite/wal/shm`, `.env*` (exceto exemplos), logs/artefatos; `git ls-files backend/data` retorna apenas `.gitkeep`; `scout.db` não versionado | **OK** |
| Scheduler | `scheduler_enabled=False` por padrão (`config.py`, `test_config.py`); sem ativação nesta etapa | **OK** |
| Coleta automática não autorizada | Scheduler desabilitado; validação API usou apenas GETs; testes que acessam rede externa foram execuções explícitas de teste (Decisão 4 confirmada, limites conservadores) | **OK** no runtime padrão; **ressalva** inerente à suíte de testes |
| APIs comerciais / dependências externas em runtime | Sem integrações pagas; saídas previstas para fontes autorizadas/configuradas e serviços locais (Ollama). Suite de testes depende do feed público W3C confirmado | **OK** para runtime; **ressalva** para testes |
| Frontend -> serviços locais previstos | `VITE_API_BASE_URL`/proxy para `127.0.0.1:8000`; consumo apenas de `/api/v1/*` locais no cliente | **OK** |

---

## 9. Etapa G — Compatibilidade e desempenho

| Aspecto | Evidência/observação | Avaliação |
|---|---|---|
| Python 3.9.6 | Venv em 3.9.6 (EOL upstream). `requires-python >=3.9`; dependências pinadas; ruff/mypy/pytest **passaram**; target ruff `py39`, mypy `python_version=3.9` | **Compatível e funcional atualmente**; risco crescente de suporte/segurança de ecossistema |
| Dependências | `requirements.txt/pyproject.toml` pinados (FastAPI 0.115.6, SQLAlchemy 2.0.36, Alembic 1.14.0, APScheduler 3.10.4, httpx 0.27.2, etc.); frontend deps pinadas em `package.json` | **Consistente e reproduzível no estado atual** |
| Apple Silicon | Ambiente `arm64`, execução local bem-sucedida de backend/frontend tooling | **Compatível** |
| Consumo de memória / concorrência | Não medido por teste de estresse (proibido). Arquitetura conservadora: monólito modular, scheduler off, `max_concurrent_jobs=1`, sem paralelismo pesado, sem inferência automática | **Adequado por desenho**, porém execução simultânea de backend + frontend dev + Ollama + navegador em 8 GB pode ser justa |
| Inicialização simultânea FE/BE e Ollama | Backend validado isoladamente; frontend build/tooling ok; Ollama listener observado em `127.0.0.1:11434` (não exercitado funcionalmente) | **Viável em princípio**, não comprovado ponta-a-ponta sob carga nesta etapa |

### Recomendação fundamentada sobre atualização do ambiente Python (sem execução)
- **Recomendação:** planejar migração controlada para uma versão suportada do CPython (preferencialmente 3.11 ou 3.12 LTS de ecossistema, ou no mínimo 3.10+) em etapa dedicada e autorizada, mantendo dependências pinadas e validação completa.
- **Benefícios:** correções de segurança e bugs do runtime, melhor suporte de bibliotecas e desempenho, redução de risco de incompatibilidade futura.
- **Riscos de atualização:** possíveis quebras em dependências binárias/wheels, mudanças sutis de tipagem/stdlib/comportamento, necessidade de recriar venv e revalidar testes/mypy/ruff/build; impacto potencial em ambientes Apple Silicon se wheels indisponíveis.
- **Mitigação proposta (futura):** criar branch/ambiente isolado, atualizar pins de forma incremental, rodar suíte completa (incluindo testes com dependência externa confirmada quando autorizado) e smoke tests de API/frontend antes de adoção. **Não executar nesta etapa.**

---

## 10. Etapa H — Plano de correções (priorizado)

> **Nenhuma correção executada.** Itens abaixo são recomendações condicionadas a autorização.

### P0 — Bloqueador
*Nenhum P0 identificado.* Não foram observadas evidências de comprometimento de segurança local essencial, integridade do banco ou impossibilidade de operar os componentes essenciais da Foundation.

| Problema | Evidência | Arquivos envolvidos | Causa provável | Solução proposta | Risco da alteração | Critério de validação |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

### P1 — Necessário (antes do aceite pleno, se o objetivo for eliminar ressalvas de validação)
| Problema | Evidência | Arquivos envolvidos | Causa provável | Solução proposta | Risco da alteração | Critério de validação |
|---|---|---|---|---|---|---|
| Suíte backend não é totalmente offline/determinística (leituras HTTP reais externas) | `backend/tests/unit/test_ingestion_registry.py` (`test_source_test_connection_real_feed`), `backend/tests/unit/test_collection_pipeline.py` (3 testes com `W3C_NEWS_FEED_URL`); execução bem-sucedida porém dependente de rede | `backend/tests/unit/test_ingestion_registry.py`, `backend/tests/unit/test_collection_pipeline.py`, possivelmente `pyproject.toml`/config de testes | Testes de referência validam integração real com feed confirmado (Decisão 4) | Introduzir camada/fixtures para tornar suíte padrão offline (mocks/servidor local/fixture de payload RSS-Atom) e mover testes de rede real para marcação explícita (ex.: integração externa/opt-in), mantendo-os disponíveis | Baixo-médio: risco de reduzir cobertura de integração real se mal separado; necessidade de manter fidelidade ao contrato do conector | `pytest` padrão passa sem acesso externo; testes externos passam quando explicitamente habilitados e com rede disponível |
| Ausência de validação E2E automatizada mínima dos fluxos críticos de System/ingestão | Não há suíte E2E identificada; inspeção visual não realizada | (novos testes/configuração de E2E, ex.: Playwright/Cypress) + possivelmente ajustes pontuais de seletores/estados em `frontend/src/pages/SystemPage.tsx`, `DashboardPage.tsx` | Escopo Foundation priorizou base e testes unitários/contratuais | Adicionar smoke E2E mínimo: carregamento Dashboard/System, listagem de conectores/fontes, fluxo controlado de teste de conexão/job/run/eventos em ambiente isolado | Médio: introduz dependências/ferramentas e custo de manutenção; deve respeitar execução local e não usar serviços externos | Pipeline de validação executa E2E local com backend/DB de teste isolados e resultados determinísticos |

### P2 — Recomendado
| Problema | Evidência | Arquivos envolvidos | Causa provável | Solução proposta | Risco da alteração | Critério de validação |
|---|---|---|---|---|---|---|
| Sincronização de metadados de conector builtin ocorre em endpoints de leitura (`GET` conectores) | `backend/app/api/v1/endpoints/ingestion.py` chama `sync_builtin_connectors_to_db(db)` em `list_connectors`/`get_connector`; observado insert idempotente em `connectors` durante validação GET | `backend/app/api/v1/endpoints/ingestion.py`, `backend/app/ingestion/bootstrap.py`, opcional `app/main.py` | Conveniência para manter registry consistente sem passo explícito | Avaliar mover sync para startup/migração controlada ou comando explícito, mantendo idempotência; ou documentar explicitamente como efeito esperado de leitura | Baixo-médio: mudar momento do sync pode afetar ambientes limpos/expectativas de bootstrap | `GET` não altera estado persistente além do estritamente documentado/necessário; conectores disponíveis em instalação limpa conforme estratégia definida |
| Ambiguidade semântica: `system` marcado como não implementado em navegação/metadados apesar de monitoramento real | `frontend/src/app/routes.tsx` (`implemented:false`), `backend/app/api/v1/endpoints/system.py` (módulos placeholder) vs `frontend/src/pages/SystemPage.tsx` com integração real | `frontend/src/app/routes.tsx`, `backend/app/api/v1/endpoints/system.py`, `frontend/src/lib/api/types.ts`, docs relacionadas se necessário | Distinção entre "módulo de domínio" e "área operacional" não modelada separadamente | Introduzir estado/flag mais expressivo (ex.: `operational`, `partial`, `placeholder`) ou ajustar descrição sem alterar contratos de forma incompatível | Baixo: impacto em UI/consumidores de contrato se houver mudança de enum | UI e API comunicam claramente que System tem monitoramento/controles de plataforma, sem sugerir módulo funcional de domínio completo |
| Atualização do ambiente Python (3.9.6 EOL upstream) | `backend/.venv` em Python 3.9.6; ecossistema em evolução | `backend/pyproject.toml`, `backend/requirements*.txt`, CI/ambiente local (quando houver) | Venv herdado/estável desde implementação | Migrar para versão suportada (ex.: 3.11/3.12) em ambiente isolado, atualizar pins/testar | Médio: compatibilidade de dependências, necessidade de revalidação completa | Suíte completa, lint, typecheck e smoke API/frontend passam no novo runtime |
| Cobertura de testes não instrumentada | `pytest --cov` indisponível | `backend/pyproject.toml`, `requirements-dev.txt` (se adotado) | Ferramenta não incluída no setup | Adicionar `pytest-cov` e metas de cobertura proporcionais ao escopo crítico | Baixo: tempo de execução maior | Relatório de cobertura gerado e integrado à validação |

### P3 — Futuro
| Problema | Evidência | Arquivos envolvidos | Causa provável | Solução proposta | Risco da alteração | Critério de validação |
|---|---|---|---|---|---|---|
| Execução concorrente completa (backend+frontend+Ollama) em 8 GB não validada | Limitação declarada do hardware; sem stress test | N/A (operacional) | Restrição de escopo/segurança desta etapa | Medir uso de memória/CPU em perfil de uso real, ajustar concorrência/cache/modelo Ollama se necessário | N/A (planejamento) | Operação estável em perfil-alvo documentado |
| Evolução para contratos/módulos de domínio (Dossiers etc.) exigirá expansão controlada | Áreas funcionais em placeholder; schema atual focado em Foundation/ingestão/rastreabilidade | múltiplos (a definir em escopo aprovado) | Próxima fase de produto | Projetar migrações, endpoints, serviços e UI por módulo com preservação de proveniência e testes | Variável (médio/alto conforme escopo) | Critérios de aceite por módulo aprovados e atendidos |

---

## 11. Parecer técnico e critérios de aceite

### 11.1 Avaliação por critério
- **Componentes essenciais validados:** backend (lint/type/tests), API (startup e endpoints principais em loopback), DB (integridade, schema, migração head, PRAGMAs de runtime), frontend (type/lint/build e integração por inspeção), segurança local básica e configuração conservadora. **Sim, com evidências.**
- **Problemas impeditivos:** **não identificados** para estabilidade/integridade/segurança essencial da Foundation no escopo atual.
- **Pendências documentadas e tratáveis sem comprometer próxima etapa:** dependência externa em testes, ausência de E2E/inspeção visual, semântica menor de status System, considerações de Python/memória e sync de conector em GET. **Sim.**

### 11.2 Classificação

**Classificação: APROVADA COM RESSALVAS**

**Justificativa (evidências):** revalidação bem-sucedida das camadas críticas (pytest 18/18, ruff/mypy/tsc/eslint/build, API operacional em `127.0.0.1` com contratos e DB em estado consistente `426757a848bb`, integridade SQLite OK, controles locais/scheduler default off preservados). Ressalvas remanescentes são de cobertura/validação operacional e manutenção de ambiente, não indicam quebra funcional da Foundation implementada.

---

## 12. Condição para avançar ao módulo Dossiers

A Foundation oferece base local-first modular com API versionada, persistência SQLite migrada (Alembic), ORM/modelo extensível com proveniência/rastreabilidade, separação frontend-backend tipada, mecanismos de auditoria/eventos e pipeline/registry de ingestão — elementos necessários para receber evolução incremental sem reconstrução de infraestrutura, desde que mudanças sejam planejadas (novas migrações, contratos e testes).

### Respostas objetivas

1. **A Foundation está pronta para receber Dossiers?**  
   **Sim, com ressalvas.** Pronta para iniciar implementação controlada de Dossiers sobre a infraestrutura existente, desde que o escopo inicial respeite o modelo atual, inclua migrações versionadas/testes e mantenha controles de proveniência, segurança local e rastreabilidade.

2. **Quais problemas precisam ser corrigidos antes?**  
   **Nenhum bloqueador (P0).** Antes de um *aceite pleno sem ressalvas de validação*, recomenda-se tratar os itens **P1** (tornar suíte padrão offline/determinística e estabelecer smoke E2E mínimo) para garantir feedback confiável durante o desenvolvimento de Dossiers.

3. **Quais podem ser adiados?**  
   **P2/P3:** ajuste semântico de status de System/rotas, revisão do momento de sync de conectores em leituras, instrumentação de cobertura, atualização planejada de Python, medições de desempenho em 8 GB e demais melhorias evolutivas não essenciais à implementação inicial controlada de Dossiers.

4. **Qual seria a sequência mínima de correções?**  
   1) **P1a:** segregar/mocar dependências externas na suíte padrão (manter teste real opcional).  
   2) **P1b:** adicionar smoke E2E local mínimo para Dashboard/System e fluxo crítico de ingestão (ambiente isolado).  
   3) (Opcional, recomendado antes de ampliar escopo) **P2:** clarificar sync de conectores em GET e semântica de `system`, com validação de não regressão.

5. **Qual é o risco de começar Dossiers imediatamente?**  
   **Risco baixo a moderado, gerenciável.** A base técnica é estável, mas: (a) feedback automatizado pode ser menos confiável/offline devido a testes dependentes de rede; (b) ausência de E2E aumenta chance de regressões de integração/UI passarem despercebidas; (c) expansão de schema/contratos sem disciplina de migração/teste pode introduzir inconsistências; (d) em 8 GB, adicionar carga (Ollama + dev servers + novas features) pode pressionar recursos. Com migrações versionadas, testes por mudança e controle de escopo, o risco é aceitável para início incremental.

---

**Encerramento:** diagnóstico e plano apresentados. **Nenhuma correção foi executada.** Aguardando autorização explícita para qualquer ação corretiva, alteração adicional de arquivos, commit/push ou avanço para Dossiers.
