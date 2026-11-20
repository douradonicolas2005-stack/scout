# DOSSIERS — Changelog

## D2 — Research & Evidence (implementado, incremental)
- **Modelo/migrações (aditivas, pós-`b7d1e2f3a4c5`):** `research_sources` (M1 `c1d2e3f4a5b6`), extensão de `documents` + `document_entity_links` (M2 `d2e3f4a5b6c7`), extensão de `extracted_claims` + `claim_entity_links` (M3 `e3f4a5b6c7d8`), `claim_conflicts` (M4 `f4a5b6c7d8e9`), extensão de `evidence` (M5 `a5b6c7d8e9f0`). Compatibilidade D1/Foundation preservada; migrações validadas em DB temporário.
- **Domínio/serviço:** cadastro e consulta determinísticos (manual-first) de fontes de pesquisa, documentos/referências, afirmações, evidências e conflitos com proveniência, âncoras, estados epistemológicos/verificação, vínculos a entidades e rastreabilidade (`audit_events`/`data_changes` e `processing_events` quando aplicável). Sem promoção automática de inferência/hipótese/previsão a fato; conflitos registrados/atualizados explicitamente com recomputo determinístico de estado.
- **API:** endpoints D2 sob `/api/v1/dossiers` para fontes de pesquisa, documentos e vínculos por entidade, afirmações, evidências, conflitos e resumo determinístico do Research Workspace.
- **Frontend:** Research Workspace na seção “Pesquisa e evidências” da página da entidade (resumo, documentos, fontes, afirmações/evidências, conflitos) com formulários e estados reais, sem simulação; D3–D5 permanecem placeholders.
- **Testes:** `backend/tests/unit/test_dossiers_research.py` (migração, CRUD/listagem, vínculo/rastreabilidade, guarda epistemológica, evidências, conflitos e resumo) + regressão Foundation/D1 verde; validações frontend (`typecheck`/`lint`/`build`) verdes.
- **Limitações intencionais:** sem agentes/coleta autônoma/indiscriminada, sem dependências pagas/comerciais obrigatórias, sem upload remoto dedicado, sem D3–D5, sem fusão automática de entidades e sem promoção automática a fato.

## D1 — Entity Profiles (implementado)
- **Modelo/migração:** extensão aditiva de `entities` (`description`, `profile_status`, `primary_location`, `profile_data`) e novas tabelas `entity_identifiers`, `entity_aliases` (Alembic `b7d1e2f3a4c5`, filha de `426757a848bb`), com índices/FKs para consulta e rastreabilidade.
- **Backend/API:** schemas e endpoints em `/api/v1/dossiers/entities` (criar, listar/pesquisar, detalhar, atualizar, sugerir duplicidades) com normalização, validação, auditoria (`audit_events`) e registro de alterações (`data_changes`).
- **Duplicidades:** detecção determinística por nome/aliases/identificadores normalizados com motivos e nível indicativo; **sem fusão automática**.
- **Frontend:** home Dossiers com pesquisa/filtros/listas e estados reais; página individual `/dossiers/:entityId` com cabeçalho, seções Visão geral/Informações funcionais e seções Histórico/Relações/Evidências e documentos/Insights como futuras (sem simulação); criação/edição e painel de duplicidades.
- **Testes/docs:** cobertura automatizada D1 adicionada; documentação do módulo criada em `docs/modules/dossiers/`.

## Próximas subetapas (pendentes de autorização)
- D3 Relationship History, D4 Connections, D5 Strategic Insights, D6 consolidação.
