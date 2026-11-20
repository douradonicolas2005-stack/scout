# DOSSIERS — Plano de Testes (D1, D2, D3)

## Escopo
Validação incremental do módulo Dossiers: D1 (Entity Profiles), D2 (Research & Evidence) e D3 (Relationship History) com modelo/migrações aditivas, API/serviços determinísticos, rastreabilidade, UI sem simulação e regressão Foundation.

## Backend (pytest, DB temporário via Alembic, sem DB real)

### D1 (implementado)
- Migração/modelo D1 sobre `426757a848bb`; CRUD de perfis, normalização/validação, pesquisa/filtros/paginação, duplicidades sugeridas sem fusão, rastreabilidade (`audit_events`/`data_changes`), regressão Foundation.
- Arquivo: `backend/tests/unit/test_dossiers_entities.py`.

### D2 (implementado)
- Migração/modelo M1–M5 sobre `b7d1e2f3a4c5`; criação de `research_sources`, extensões/links de `documents` e `extracted_claims`, `claim_conflicts`, extensão de `evidence`.
- Fontes de pesquisa: criar/listar/consultar/atualizar; validação e rastreabilidade.
- Documentos: exigência de âncora de proveniência, criação/consulta/listagem por entidade, associação entidade-documento, atualização e rastreabilidade.
- Afirmações: criação manual vinculada à entidade, classificação/estados/proveniência; guarda epistemológica (inferência/hipótese/previsão marcada como verificada exige justificativa explícita).
- Evidências: criação vinculada à afirmação com relação/âncoras e rastreabilidade.
- Conflitos: registro explícito entre afirmações, atualização de status e recomputo determinístico do estado de conflito; listagem por entidade.
- Resumo de workspace: indicadores determinísticos consistentes com dados persistidos.
- Arquivo: `backend/tests/unit/test_dossiers_research.py` (offline, DB temporário).

### D3 (implementado em working tree, validado nesta revisão)
- Migração/modelo D3 (`b6c7d8e9f0a1`) sobre `a5b6c7d8e9f0`; tabela `entity_interactions` (natureza/estado/temporalidade/contexto/proveniência opcional) criada e consultável.
- CRUD/timeline: criação, listagem por entidade, detalhe e atualização explícita (estado/natureza/verificação) com persistência.
- Naturezas: suporte e rotulagem de `declarado`, `observado`, `interpretado`, `a_confirmar` (sem promoção automática a fato).
- Filtros/ordenação/busca: por natureza, tipo, status, texto e ordenação (ex.: ocorrência desc/asc).
- Proveniência/referências opcionais: persistência de referências (documento, fonte de pesquisa, raw record, afirmação, evidência, localizador) quando válidas; **validação de integridade** rejeita referências inexistentes.
- Validações: natureza obrigatória/válida, título/tipo obrigatórios, coerência temporal (`ended_at >= started_at`), confiança em [0,1], entidade/interação inexistente (404/422 conforme caso).
- Rastreabilidade: `audit_events` e `data_changes` em criação/atualização.
- Resumo determinístico: contagens/distribuições e pendências derivados de dados persistidos.
- Arquivo: `backend/tests/unit/test_dossiers_history.py` (offline, DB temporário).

## Frontend
- `npm run typecheck`, `npm run lint`, `npm run build` sem erros.
- Revisão de implementação: Home/D1, Research Workspace D2 e History Workspace D3 consomem API real, rotulam epistemologia/natureza/estados, mantêm D4–D5 como placeholders sem simulação e preservam estados loading/erro/vazio.
- **Validação manual assistida / smoke test (navegador/UI):** executado em 19/11/2026 (frontend Vite local em 127.0.0.1:5174 + backend local em 127.0.0.1:8000, browser in-app). Fluxos verificados: abertura do dossiê e seção Histórico, carregamento de resumo/timeline/lista, exibição das quatro naturezas (`declarado`, `observado`, `interpretado`, `a_confirmar`) e estados, detalhe com proveniência/referências opcionais (documento, fonte de pesquisa, afirmação, evidência, localizador), ações explícitas de estado visíveis e ausência de erros de console com respostas 200 nos endpoints de interações. Criação, edição, filtros/ordenação, atualizações explícitas e rastreabilidade/persistência foram validados via API e refletidos na UI após recarregamento.

## Regressão e execução
- Regressão Foundation + D1 + D2 + D3 verde na suíte backend (`pytest`) e validações frontend.
- Migrações validadas em banco temporário (`alembic upgrade head` até `b6c7d8e9f0a1`) e verificação do head do DB local.
- Observação: testes legados de ingestão (Decisão 4) executam de forma offline/determinística por ajuste de fixture/mock; novos testes D2/D3 não dependem de rede.

## Critérios de aceite (D1–D3)
- D1 funcional e persistente, sem fusão automática.
- D2 registra/consulta fontes, documentos, afirmações, evidências e conflitos com proveniência, estados explícitos e rastreabilidade; sem promoção automática a fato e sem simulação.
- D3 registra/consulta/atualiza interações em timeline com natureza explícita, proveniência opcional, estados e rastreabilidade; sem promoção automática a fato, sem derivação automática e sem uso de `relationships` (D4).
- Migrações aditivas válidas; compatibilidade Foundation/D1/D2 preservada.
