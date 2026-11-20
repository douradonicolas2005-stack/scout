# DOSSIERS — Plano de Testes (D1, D2)

## Escopo
Validação incremental do módulo Dossiers: D1 (Entity Profiles) e D2 (Research & Evidence) com modelo/migrações aditivas, API/serviços determinísticos, rastreabilidade, UI sem simulação e regressão Foundation.

## Backend (pytest, DB temporário via Alembic, sem DB real)
### D1 (implementado)
- Migração/modelo D1 sobre `426757a848bb`; CRUD de perfis, normalização/validação, pesquisa/filtros/paginação, duplicidades sugeridas sem fusão, rastreabilidade (`audit_events`/`data_changes`), regressão Foundation.

### D2 (implementado)
- **Migração/modelo:** aplicação de M1–M5 sobre `b7d1e2f3a4c5` em DB temporário; criação de `research_sources`, `document_entity_links`, `claim_entity_links`, `claim_conflicts` e extensões de `documents`/`extracted_claims`/`evidence`; uso básico de colunas/defaults.
- **Fontes de pesquisa:** criar/listar/consultar/atualizar; validação e rastreabilidade.
- **Documentos:** exigência de âncora de proveniência, criação/consulta/listagem por entidade, associação entidade-documento, atualização e rastreabilidade.
- **Afirmações:** criação manual vinculada à entidade, classificação/estados/proveniência; guarda epistemológica (inferência/hipótese/previsão marcada como verificada exige justificativa explícita).
- **Evidências:** criação vinculada à afirmação com relação/âncoras e rastreabilidade.
- **Conflitos:** registro explícito entre afirmações, atualização de status e recomputo determinístico do estado de conflito; listagem por entidade.
- **Resumo de workspace:** indicadores determinísticos consistentes com dados persistidos.

Arquivo de testes D2: `backend/tests/unit/test_dossiers_research.py` (offline, DB temporário).

## Frontend
- `npm run typecheck`, `npm run lint`, `npm run build` sem erros.
- Revisão de implementação: Research Workspace D2 consome API real, rotula epistemologia/conflitos, mantém D3–D5 como placeholders sem simulação e preserva estados loading/erro/vazio.

## Regressão e execução
- Regressão Foundation + D1 mantida verde na suíte backend (`pytest`) e validações frontend.
- Observação de ambiente: a suíte completa do repositório inclui testes legados com acesso HTTP real ao feed público da Decisão 4; execução requer rede quando esses testes rodam. Novos testes D2 não dependem de rede.

## Critérios de aceite (D1+D2)
- D1 funcional e persistente, sem fusão automática.
- D2 registra/consulta fontes, documentos, afirmações, evidências e conflitos com proveniência, estados explícitos e rastreabilidade; sem promoção automática a fato e sem simulação de dados/funções futuras.
- Migrações aditivas válidas; compatibilidade D1/Foundation preservada.
