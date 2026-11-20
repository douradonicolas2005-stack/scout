# DOSSIERS — Changelog

## D3 — Relationship History (implementado, validado e publicado)
- **Modelo/migração (aditiva, pós-`a5b6c7d8e9f0`):** `b6c7d8e9f0a1_d3_relationship_history` cria `entity_interactions` (interações por entidade com tipo, título/descrição, natureza obrigatória `declarado|observado|interpretado|a_confirmar`, status, temporalidade/precisão, contexto, proveniência/referências opcionais, confiança/justificativa, verificação e metadados) com FKs/índices; migração aplicada ao DB local (head `b6c7d8e9f0a1`) e validada em DB temporário.
- **Domínio/serviço:** CRUD/listagem/filtros/ordenação e resumo determinístico de interações por entidade, com validações (natureza/temporalidade/confiança), integridade de referências opcionais, distinção D3≠D2 e sem uso de `relationships` (reservado a D4); rastreabilidade via `audit_events`/`data_changes`. Sem promoção automática a fato e sem derivação automática.
- **API:** endpoints em `/api/v1/dossiers` — criar/listar interações por entidade, detalhar/atualizar interação e resumo determinístico (`/entities/{entity_id}/interactions`, `/entities/{entity_id}/interactions/summary`, `/interactions/{interaction_id}`).
- **Frontend:** `HistoryWorkspace` na seção **Histórico** da página da entidade (timeline, filtros/ordenação, registro, detalhe, ações explícitas de estado e proveniência opcional) com estados reais e sem simulação; D4/D5 permanecem placeholders.
- **Testes/validação:** `backend/tests/unit/test_dossiers_history.py` (migração/modelo, CRUD/timeline/filtros/ordenação, naturezas, atualização explícita, resumo, rastreabilidade, validações e integridade de referências). Correção aplicada na revisão: validação explícita de existência de referências opcionais. Suíte e validações estáticas/build verdes; validação funcional assistida via API e **smoke test de UI em navegador** concluídos (timeline/resumo, naturezas/estados, detalhe com proveniência/referências, ações explícitas, sem erros de console e endpoints 200).
- **Estado:** **formalizado e publicado** em `origin/main`, com documentação de módulo/projeto e auditoria atualizadas. D4–D6 permanecem fora de escopo (D4 condicionado a planejamento técnico aprovado).

## D2 — Research & Evidence (implementado, incremental)
- **Modelo/migrações (aditivas, pós-`b7d1e2f3a4c5`):** `research_sources` (M1 `c1d2e3f4a5b6`), extensão de `documents` + `document_entity_links` (M2 `d2e3f4a5b6c7`), extensão de `extracted_claims` + `claim_entity_links` (M3 `e3f4a5b6c7d8`), `claim_conflicts` (M4 `f4a5b6c7d8e9`), extensão de `evidence` (M5 `a5b6c7d8e9f0`). Compatibilidade D1/Foundation preservada; migrações validadas em DB temporário.
- **Domínio/serviço:** cadastro e consulta determinísticos (manual-first) de fontes de pesquisa, documentos/referências, afirmações, evidências e conflitos com proveniência, âncoras, estados epistemológicos/verificação, vínculos a entidades e rastreabilidade (`audit_events`/`data_changes` e `processing_events` quando aplicável). Sem promoção automática de inferência/hipótese/previsão a fato; conflitos registrados/atualizados explicitamente com recomputo determinístico de estado.
- **API:** endpoints D2 sob `/api/v1/dossiers` para fontes de pesquisa, documentos e vínculos por entidade, afirmações, evidências, conflitos e resumo determinístico do Research Workspace.
- **Frontend:** Research Workspace na seção “Pesquisa e evidências” da página da entidade (resumo, documentos, fontes, afirmações/evidências, conflitos) com formulários e estados reais, sem simulação; D3–D5 permaneceram placeholders até D3.
- **Testes:** `backend/tests/unit/test_dossiers_research.py` + regressão Foundation/D1 verde; validações frontend verdes.
- **Limitações intencionais:** sem agentes/coleta autônoma/indiscriminada, sem dependências pagas/comerciais obrigatórias, sem upload remoto dedicado, sem fusão automática e sem promoção automática a fato.

## D1 — Entity Profiles (implementado)
- **Modelo/migração:** extensão aditiva de `entities` (`description`, `profile_status`, `primary_location`, `profile_data`) e novas tabelas `entity_identifiers`, `entity_aliases` (Alembic `b7d1e2f3a4c5`, filha de `426757a848bb`).
- **Backend/API:** schemas e endpoints em `/api/v1/dossiers/entities` (criar, listar/pesquisar, detalhar, atualizar, sugerir duplicidades) com normalização, validação e rastreabilidade (`audit_events`, `data_changes`).
- **Duplicidades:** detecção determinística com motivos e nível indicativo; **sem fusão automática**.
- **Frontend:** home Dossiers e página individual `/dossiers/:entityId` com seções funcionais e futuras sem simulação; criação/edição e painel de duplicidades.
- **Testes/docs:** cobertura automatizada D1 e documentação do módulo em `docs/modules/dossiers/`.

## Próximas subetapas (pendentes de autorização)
- D4 Connections, D5 Strategic Insights, D6 consolidação.
