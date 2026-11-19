# PROJECT_STATUS — SCOUT (Foundation V1.1)

> **Data:** 2026-11-19 · **Fase:** **Subetapa H concluída** (testes, documentação e validação final). Runtime/API: `foundation-g`. Foundation V1.1 (A–H) concluída no escopo definido, aguardando aceite do usuário e confirmação/substituição da Decisão 4. **Não avançar automaticamente** para pós-Foundation.

## Resumo executivo
SCOUT Foundation V1.1 em `scout/` (decisão **1b**, V0 substituído) está implementada e validada como monólito modular **local-first** (loopback, SQLite/Alembic, sem simulações e sem inferência automática). Subetapas A–G entregaram infraestrutura full-stack, schema de 15 entidades, integração frontend-backend de estado, Source Registry/conector real `rss_atom`, pipeline mínimo rastreável de coleta com scheduler conservador (estado canônico no banco, desabilitado por padrão) e monitoramento operacional mínimo em **System**. Subetapa H consolidou os 9 documentos, reforçou validações e registrou limitações/decisões pendentes, sem ampliar escopo funcional de domínio/inteligência/predição.

## Decisões aplicadas (aprovadas)
- **1b:** substituir V0 em `scout/`.
- **2:** SQLAlchemy 2.0 + Pydantic (schemas separados).
- **3:** APScheduler (Background, conservador) + estado/agendamento canônico no banco.
- **5:** Ollama — abstração + configuração + verificação de disponibilidade sob demanda; **sem inferência automática** em testes/execução.
- **6:** `pyproject.toml` + `requirements.txt`/`requirements-dev.txt` pinados.

## Decisão pendente
- **4 — Recurso de referência real (auto-aplicada, pendente de confirmação/substituição explícita):** URLs iniciais (`https://exemplo.org/feed.xml`, `https://<dominio>/<feed>.xml`) eram inválidas/placeholders. Com autorização explícita prévia para prosseguir automaticamente sem confirmação, foi utilizado **`https://www.w3.org/news/feed/`** (RSS/Atom, público, W3C News) para teste/leitura/coleta real local.
  - **Restrições:** somente leitura, metadados/títulos, **máx. 5 itens**, timeouts e limite de tamanho; sem preservação de corpo/conteúdo completo nos testes/pipeline padrão (preservação condicional apenas quando explicitamente permitida por configuração/permissões/licença).
  - **Status:** validado funcionalmente nas Subetapas E/F/G e exercitado pela suíte de testes backend existente. **Confirmar** permanência ou **substituir** por RSS/Atom/HTTP GET explicitamente autorizado.

## Implementado (por subetapa)

### A — Estrutura e ambiente local
- Monorepo `backend/`, `frontend/`, `docs/`, envs/gitignore/README, App Shell e Design System base (Tailwind/shadcn, temas), navegação das 8 áreas como placeholders sem simulação, cliente API e `GET /api/v1/health`.

### B — Backend e banco de dados
- SQLite com PRAGMAs (`foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000`), storage `backend/data/raw/` e `backend/data/documents/`.
- Alembic revisão `426757a848bb` (`foundation_b_schema`) criando 15 tabelas/índices.
- ORM (15): `sources`, `connectors`, `collection_jobs`, `collection_runs`, `raw_records`, `documents`, `extracted_claims`, `evidence`, `entities`, `relationships`, `data_changes`, `processing_events`, `agent_runs`, `audit_events` com proveniência/qualidade/versionamento e semântica de claim/verificação.
- **Regra preservada:** inferência **não** promovida a fato automaticamente.
- Endpoints base: `GET /api/v1/system/info`, `GET /api/v1/db/status`.

### C — Frontend e Design System
- Paleta/tokens SCOUT, temas claro/escuro com persistência (`scout-theme`, padrão escuro) e bootstrap anti-flash.
- App Shell responsivo (sidebar/drawer), breadcrumbs, pesquisa global **desabilitada/read-only** (sem simulação), `PageState`/`PageHeader`, acessibilidade básica (skip link, foco visível, labels/aria).

### D — Integração frontend-backend
- Tipos/cliente API para `health`, `system/info`, `db/status`.
- Dashboard e System consomem estado real com tratamento de loading/erro/vazio/sucesso (sem simular funcionalidades).

### E — Source Registry e conectores
- CRUD/ativação de fontes e registro/sincronização de conectores em `/api/v1/ingestion/*` com validação e coerência `status`↔`is_active`.
- Conectores plugáveis + **`rss_atom`** real (RSS/Atom, read-only, metadados/títulos, máx. 5 itens, limites/timeouts).
- `POST /sources/{id}/test-connection` real com rastreabilidade (`audit_events`, `processing_events stage=connection_test`), sem jobs/runs de coleta.

### F — Scheduler e pipeline de ingestão (mínimo)
- Pipeline (`app/ingestion/collection.py`): `collection_jobs`/`collection_runs`, estágios rastreáveis, coleta real via conector registrado, normalização/validação básica, deduplicação, persistência de `raw_records`, `data_changes`, `processing_events`, atualização de estados/métricas/`last_collected_at`, retries conservadores.
- Preservação condicional de original em `backend/data/raw/<source_id>/` apenas quando permitido por config/permissões/licença.
- Scheduler (`app/ingestion/scheduler.py`): APScheduler Background, **desabilitado por padrão**, estado/agendamento canônico no banco, reidratação controlada, sem paralelismo pesado; execução manual via API.
- Endpoints: criar/listar/consultar/executar jobs, listar runs e eventos.

### G — Source Manager e monitoramento (mínimo)
- `GET /api/v1/system/audit-events` (leitura de auditoria recente).
- UI **System** (`frontend/src/pages/SystemPage.tsx`) com visão real de conectores/fontes/jobs/runs/eventos/auditoria e controles mínimos (testar conexão, criar job com `execute_now`, executar job, inspecionar histórico/erros), com estados loading/erro/vazio/sucesso e sem simulação.
- Fase de runtime: `foundation-g`.

### H — Testes, documentação e validação final
- Consolidação/alinhamento dos 9 documentos com estado implementado (A–G), lacunas, restrições e decisões pendentes.
- Validações finais backend/frontend e correções de consistência detectadas.
- Relatório de encerramento da Foundation V1.1 (este documento).

## Verificações finais executadas (Subetapa H)

| # | Verificação | Comando / método | Resultado |
|---|---|---|---|
| 1 | Backend — lint | `cd backend && .venv/bin/ruff check app tests` | **OK** (All checks passed) |
| 2 | Backend — tipagem | `.venv/bin/mypy app` | **OK** (Success, 53 source files) |
| 3 | Backend — testes (regressão + integração/pipeline real) | `.venv/bin/python -m pytest -q` | **18 passed** (0.93s) |
| 4 | Frontend — tipagem | `cd frontend && npm run typecheck` | **OK** |
| 5 | Frontend — lint | `npm run lint` | **OK** |
| 6 | Frontend — build | `npm run build` | **OK** (1627 módulos) |
| 7 | Schema/migração | Reutilização do schema existente (sem nova migração) | **OK** — `426757a848bb foundation_b_schema` |

**Notas de validação:**
- Suíte backend preservada (health/config/db/system, registry/CRUD/teste real de conexão, pipeline real, deduplicação, `execute_now=false`, dispatch do scheduler a partir do banco) com expectativas de fase `foundation-g`.
- A suíte inclui acesso HTTP real de leitura (metadados/títulos, limites conservadores) ao recurso da Decisão 4 (`https://www.w3.org/news/feed/`), conforme validações estabelecidas em E/F/G.
- Não foram executados testes E2E de navegador automatizados nem testes manuais interativos de UI nesta sessão, além das verificações estáticas/build do frontend.

## Arquivos alterados/criados relevantes (estado consolidado)

### Subetapa H (documentação/validação)
- **Alterados:** `README.md`, `docs/VISION.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, `docs/DESIGN_SYSTEM.md`, `docs/API.md`, `docs/INGESTION_ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/ROADMAP.md`, `docs/PROJECT_STATUS.md`, `frontend/src/pages/SystemPage.tsx` (correção estrutural/consistência da UI de monitoramento para estado válido de build).

### Subetapas anteriores (resumo)
- **G:** `backend/app/api/v1/{schemas,endpoints}/audit.py`, `backend/app/api/router.py`, endpoints `health/system`/`main`/scheduler (fase), testes de sistema/health, `frontend/src/lib/api/{types,client}.ts`, `frontend/src/pages/SystemPage.tsx`, docs.
- **F:** `backend/app/ingestion/{collection.py,scheduler.py,pipeline}`, schemas/endpoints de jobs/runs/eventos, testes de pipeline, integração API/lifespan, docs.
- **E:** schemas/endpoints de ingestão, `ingestion/bootstrap.py`, `connectors/rss_atom.py`, testes de registry/conector, docs.
- **D:** integração frontend tipada (`api/types,client`, Dashboard/System).
- **C:** consolidação frontend/Design System/App Shell/componentes/estados.
- **B:** 15 modelos ORM, migração `426757a848bb`, endpoints `system/info` e `db/status`, storage/pragmas, testes DB/estado.
- **A:** estrutura base backend/frontend/docs e esqueleto de camadas/navegação.

## Problemas encontrados e correções (síntese)
- **G/H (frontend):** erros de TypeScript/lint/build em `SystemPage.tsx` (uso de `toLower()` e `res.run` possivelmente nulo) e corrupção de estrutura JSX em patch programático subsequente; corrigidos com tratamento defensivo e restauração de componente íntegro. Resultado: `typecheck/lint/build` **OK**.
- **F:** ajustes de `ruff/mypy`, compatibilidade `Optional` (Python 3.9) e re-fetch após rollback no tratamento de erro do pipeline; suíte **OK**.
- **E:** URLs iniciais da Decisão 4 inválidas/placeholders (auto-aplicação autorizada de recurso público) e ajustes de lint/tipagem; testes reais **OK**.
- **B–D:** correções pontuais de migração/env, tipagem/lint e reaplicação de edições frontend; verificações **OK** nas respectivas etapas.
- **Estado atual:** nenhuma falha de verificação remanescente conhecida no escopo validado.

## Limitações e pendências
- **Decisão 4 pendente:** confirmar/substituir `https://www.w3.org/news/feed/`.
- **Banco local:** preparar com `cd backend && .venv/bin/alembic upgrade head` (sem novas migrações em E/F/G/H).
- **Monitoramento/UI (mínimo):** implementado em **System**; sem CRUD completo de fontes no frontend, sem controles avançados (cancelamento/edição/agendamento rico, filtros/paginação/métricas consolidadas), sem UI dedicada fora de System.
- **Pipeline/domínio:** sem `documents` derivados, extração/claims/evidências/entidades/relacionamentos e encaminhamento completo; sem inferência automática e sem promoção de inferência a fato.
- **Scheduler:** conservador, DB-canonical, reidratação controlada disponível, porém **desabilitado por padrão** (`scheduler_enabled=false`).
- **Módulos funcionais/inteligência/predição/simulação:** não implementados (8 áreas como placeholders, sem simulação).
- **Testes:** sem E2E de navegador e sem suíte automatizada específica adicional para a UI/auditoria de G além de validação estática/build.

## Riscos observados
- Python 3.9.6 (EOL upstream) — funcional; recomenda-se padronizar versão suportada futuramente.
- RAM 8 GB: manter concorrência controlada e dependências mínimas (sem inferência pesada/paralelismo).
- Dependências de desenvolvimento podem requerer auditoria/atualização em etapa dedicada.

## Conclusão (Foundation V1.1)
- **Escopo A–H:** concluído e validado conforme critérios da Foundation (infraestrutura local, rastreabilidade, controles conservadores, contratos reais, sem simulações e sem inferência automática).
- **Próximo passo:** aguardando **aceite do usuário** e **confirmação/substituição da Decisão 4**. Qualquer evolução pós-Foundation (controles/monitoramento avançados, domínio/extração/grafo, módulos funcionais, inteligência/predição) requer escopo e aprovação explícitos.
- **Não avançarei automaticamente.**
