# PROJECT_STATUS — SCOUT (Foundation V1.1)

> **Data:** 2026-11-19 · **Fase:** **Subetapa H concluída** (Foundation). Runtime/API: `foundation-g`. **Dossiers D1/D2 entregues; D3 validado (incluindo smoke test de UI), formalizado e publicado.** **Decisão 4 confirmada** (`https://www.w3.org/news/feed/`, limites conservadores). **Não avançar para D4 sem planejamento técnico aprovado.**

## Resumo executivo
SCOUT Foundation V1.1 em `scout/` (decisão **1b**) está implementada e validada como monólito modular **local-first** (loopback, SQLite/Alembic, sem simulações e sem inferência automática). O módulo Dossiers evoluiu incrementalmente: **D1 (Entity Profiles)** e **D2 (Research & Evidence)** entregues; **D3 (Relationship History)** implementado, revisado, validado (suíte automatizada, validação funcional assistida via API e smoke test de UI em navegador) e **publicado** (commit/push), com correção de integridade de referências opcionais aplicada na revisão. D4 permanece pendente de planejamento técnico aprovado.

## Estado de repositório e banco (verificado em 2026-11-19)
- **Publicado:** D3 commitado e enviado a `origin/main` (`feat(dossiers): implement D3 relationship history`), incluindo migração `b6c7d8e9f0a1`, domínio/API/UI/testes, correção de integridade e documentação/auditoria atualizada.
- **Working tree:** limpo após publicação (sem alterações D3 pendentes).
- **DB local:** `scout/backend/data/scout.db` (gitignored) em Alembic head **`b6c7d8e9f0a1`** (migração D3 aplicada localmente). Dados locais preservados.

## Decisões e restrições preservadas
- **1b:** substituir V0 em `scout/`. **2:** SQLAlchemy 2.0 + Pydantic. **3:** APScheduler conservador, DB-canonical, desabilitado por padrão. **5:** Ollama abstração/disponibilidade sob demanda, sem inferência automática. **6:** `pyproject.toml` + requirements pinados.
- **Decisão 4:** `https://www.w3.org/news/feed/` (W3C News RSS, público, read-only, metadados, máx. 5 itens, timeouts/limites). Eventual substituição/inclusão requer nova autorização explícita.
- **Restrições:** local-first, determinístico, rastreável, sem promoção automática de inferência a fato, sem fusão automática, sem agentes/coleta autônoma ou indiscriminada, sem dependências pagas/comerciais obrigatórias, sem paralelismo pesado, UI sem simulação.

## Implementado

### Foundation V1.1 (A–H) — concluída e validada
- Infra full-stack, schema de 15 entidades e migração `426757a848bb`, Design System/App Shell, integração frontend-backend, Source Registry/conector `rss_atom`, pipeline mínimo rastreável/scheduler conservador, monitoramento operacional mínimo em **System** e consolidação documental/validações.

### Dossiers V1.0 — D1: Entity Profiles (entregue)
- Migração aditiva `b7d1e2f3a4c5`; extensão de `entities` e tabelas `entity_identifiers`/`entity_aliases`.
- API `/api/v1/dossiers/entities*` (CRUD, pesquisa/filtros/paginação/sort, duplicidades sugeridas sem fusão) com rastreabilidade (`audit_events`, `data_changes`).
- UI Home Dossiers e página da entidade (visão geral/informações, criação/edição, duplicidades).

### Dossiers V1.0 — D2: Research & Evidence (entregue)
- Migrações aditivas `c1d2e3f4a5b6` → `a5b6c7d8e9f0`: `research_sources`, extensões/links de `documents` e `extracted_claims`, `claim_conflicts`, extensão de `evidence`.
- API/serviços determinísticos para fontes, documentos, afirmações, evidências, conflitos e resumo do Research Workspace; guarda epistemológica (sem promoção automática a fato).
- UI Research Workspace integrado à página da entidade, com estados reais e sem simulação.

### Dossiers V1.0 — D3: Relationship History (implementado em working tree, validado)
- **Modelo/migração:** `b6c7d8e9f0a1_d3_relationship_history` cria `entity_interactions` (natureza `declarado|observado|interpretado|a_confirmar`, status, temporalidade/precisão, contexto, participantes descritivos, proveniência/referências opcionais, confiança/justificativa, verificação) com FKs/índices. Distinto de D2; **não usa `relationships`** (reservado a D4).
- **Backend/API:** `history_service`, schemas e endpoints em `/api/v1/dossiers` (`POST/GET /entities/{entity_id}/interactions`, `GET /entities/{entity_id}/interactions/summary`, `GET/PATCH /interactions/{interaction_id}`) com validações, filtros/ordenação/paginação, resumo determinístico e rastreabilidade (`audit_events`, `data_changes`).
- **Frontend:** `HistoryWorkspace` na seção **Histórico** (timeline, filtros, registro, detalhe, ações explícitas de estado, proveniência opcional, estados reais). D4/D5 permanecem placeholders.
- **Correção aplicada na revisão:** validação explícita de existência de referências opcionais (`document_id`, `research_source_id`, `raw_record_id`, `claim_id`, `evidence_id`) no serviço para garantir integridade consistente.

## Validações executadas (revisão D3, 2026-11-19)

| # | Verificação | Resultado |
|---|---|---|
| 1 | Migrações em DB temporário | **OK** — `alembic upgrade head` até `b6c7d8e9f0a1` |
| 2 | Estado migração DB local | **OK** — `b6c7d8e9f0a1 (head)` |
| 3 | Backend — pytest (completo) | **OK** — **30 passed** (Foundation + D1 + D2 + D3) |
| 4 | Backend — ruff | **OK** (All checks passed) |
| 5 | Backend — mypy | **OK** (Success, 70 source files) |
| 6 | Frontend — typecheck | **OK** |
| 7 | Frontend — eslint | **OK** |
| 8 | Frontend — build | **OK** (1632 módulos) |
| 9 | Validação funcional assistida D3 (API/TestClient, DB temporário) | **OK** — criar/listar/editar, 4 naturezas, filtros/ordenação, referências opcionais válidas, atualizações explícitas, persistência/rastreabilidade e resumo |
| 10 | Smoke test de UI (navegador, Vite+backend local) | **OK** — Histórico abre com resumo/timeline/lista, 4 naturezas e estados visíveis, detalhe com proveniência/referências, ações explícitas de estado, sem erros de console e endpoints de interações com 200; dados persistidos/rastreados refletidos na UI |

## Problemas encontrados e correções (revisão D3)
- **Integridade de referências opcionais (corrigido):** interações aceitavam IDs de referência inexistentes no fluxo validado (risco de inconsistência quando FKs não efetivamente aplicadas pelo contexto de conexão). **Correção:** validação explícita de existência das referências opcionais no serviço (`history_service`) em criação/atualização, com retorno 404 para referência inexistente; teste D3 atualizado. Revalidação verde.

## Limitações e pendências
- **D4–D6:** pendentes (Connections/`relationships`, Strategic Insights, consolidação). D4 aguarda planejamento técnico aprovado antes de qualquer implementação.
- **Banco local:** migrado para `b6c7d8e9f0a1` (gitignored); dados locais preservados.
- Smoke test de UI realizado em cenário controlado local; automação E2E dedicada permanece opcional para evolução futura.
- Demais limitações de Foundation/pós-Foundation e riscos previamente registrados permanecem aplicáveis.

## Conclusão
- **Foundation V1.1, D1 e D2:** preservados e compatíveis (regressão verde).
- **D3:** implementado, revisado, validado (automação, API assistida e smoke test de UI) e **publicado** em `origin/main`, com correção de integridade aplicada. **Aprovado no escopo definido. Não avançar automaticamente para D4; planejamento técnico de D4 requerido.**
