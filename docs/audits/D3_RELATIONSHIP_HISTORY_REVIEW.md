# D3_RELATIONSHIP_HISTORY_REVIEW — Revisão e conclusão controlada de D3

> **Módulo:** Dossiers · **Subetapa:** D3 — Relationship History  
> **Data da revisão:** 2026-11-19  
> **Revisor:** assistente (execução controlada, sem commit/push)  
> **Escopo:** inspeção, validação funcional assistida, revisão técnica, atualização documental e validações finais de D3 (sem implementar D4/D5, sem alterar Foundation/D1/D2)

## 1. O que foi revisado

### 1.1 Alterações locais inspecionadas (working tree, sem descarte/sobrescrita)
- **Modificados:** `backend/app/api/router.py`, `backend/app/knowledge/models/__init__.py`, `backend/app/knowledge/models/domain.py`, `frontend/src/components/dossiers/utils.ts`, `frontend/src/lib/api/client.ts`, `frontend/src/lib/api/types.ts`, `frontend/src/pages/DossierEntityPage.tsx`, além de documentação e (durante a revisão) `backend/app/knowledge/dossiers/history_service.py`, `backend/tests/unit/test_dossiers_history.py`.
- **Novos (não rastreados):** `backend/app/db/migrations/versions/b6c7d8e9f0a1_d3_relationship_history.py`, `backend/app/knowledge/dossiers/history_service.py`, `backend/app/api/v1/schemas/dossiers_history.py`, `backend/app/api/v1/endpoints/dossiers_history.py`, `backend/tests/unit/test_dossiers_history.py`, `frontend/src/components/dossiers/HistoryWorkspace.tsx`, `docs/audits/D3_RELATIONSHIP_HISTORY_REVIEW.md`.
- **Base commitada comparada:** `main@0e3b05a` = `origin/main` (D1/D2 entregues). Nenhuma alteração de D3 estava commitada; D3 existia em estado local (migração já aplicada ao DB local) e foi revisado/ajustado nesta sessão.

### 1.2 Comparação com o plano técnico D3
A implementação foi confrontada com o plano técnico registrado anteriormente (D3 Relationship History) e com as restrições do projeto:
- **Modelo/migração:** `entity_interactions` aditiva (`b6c7d8e9f0a1`, filha de `a5b6c7d8e9f0`) com campos de identidade/vínculo à entidade, tipo/título/descrição, natureza obrigatória (`declarado|observado|interpretado|a_confirmar`), status, temporalidade/precisão, contexto, participantes descritivos, proveniência/referências opcionais, confiança/justificativa, verificação, metadados e timestamps; FKs/índices compatíveis. **Alinhado.**
- **Separação semântica:** D3 trata interações/timeline (distinto de D2 pesquisa/evidências) e **não utiliza/redefine `relationships`** (reservado a D4). **Alinhado.**
- **Domínio/serviço:** validações de natureza, temporalidade (`ended_at >= started_at`), confiança [0,1], campos obrigatórios, entidade existente; CRUD/listagem/filtros/ordenação/paginação e resumo determinístico; rastreabilidade via `audit_events` e `data_changes`; sem promoção automática a fato e sem derivação automática. **Alinhado (com correção de integridade aplicada, ver seção 3).**
- **Schemas/endpoints:** contratos para criação/listagem/detalhe/atualização e resumo sob `/api/v1/dossiers`. **Alinhado.**
- **Frontend:** `HistoryWorkspace` integrado na seção “Histórico” de `DossierEntityPage` (timeline, filtros/ordenação, formulário, detalhe, ações explícitas de estado, proveniência opcional, natureza/estados rotulados, estados loading/erro/vazio/sucesso), sem simulação; D4/D5 permanecem placeholders. **Alinhado.**
- **Compatibilidade:** reuso de padrões/infra D1/D2/Foundation, sem alterações de escopo de Foundation/D1/D2 e sem introdução de D4/D5. **Alinhado.**

## 2. O que foi validado

### 2.1 Validação funcional assistida (API/serviço, TestClient + DB temporário via Alembic)
Executada em ambiente isolado (migração `upgrade head` até `b6c7d8e9f0a1`) cobrindo os fluxos solicitados:

| Fluxo solicitado | Resultado | Evidência (assistida) |
|---|---|---|
| 1. Criar interação vinculada a uma entidade | **OK** | Criações bem-sucedidas (201) vinculadas à entidade |
| 2. Consultar a timeline | **OK** | Listagem por entidade com total/itens retornados |
| 3. Editar uma interação | **OK** | `PATCH` com persistência de alterações (título/descrição/campos) |
| 4. Testar as quatro naturezas (`declarado`, `observado`, `interpretado`, `a_confirmar`) | **OK** | Registros criados e recuperados para as quatro naturezas |
| 5. Testar filtros e ordenação | **OK** | Filtros por `nature`, `interaction_type`, `status`, busca `q` e ordenação `occurred_asc` |
| 6. Testar referências opcionais a documentos, fontes, afirmações e evidências | **OK** | Interação com `document_id`, `research_source_id`, `claim_id`, `evidence_id` e `source_locator` válidos persistida e recuperada |
| 7. Testar estados e atualizações explícitas | **OK** | Atualização explícita de `status`, `nature` e `verification_status` persistida e rastreável |
| 8. Verificar persistência e rastreabilidade | **OK** | `interactions/summary` consistente; `audit_events` e `data_changes` registrados (create/update) |

> **Nota (navegador/UI):** não foi possível executar validação visual/funcional em navegador nesta revisão (sem sessão interativa de app frontend+backend em execução no ambiente). **Testes manuais de UI em navegador não são declarados como aprovados.** Os fluxos acima foram validados em nível de API/serviço (assistido) e os componentes/integração de UI passaram por typecheck/lint/build.

### 2.2 Revisão técnica
- **Consistência modelo/serviço/API/schemas/UI:** campos, naturezas, estados, temporalidade e proveniência coerentes entre ORM, migração, serviço, contratos e cliente/UI.
- **Validações:** natureza obrigatória/válida, tipo/título obrigatórios, coerência temporal, confiança [0,1], entidade/interação inexistente (404/422).
- **Rastreabilidade:** `audit_events` e `data_changes` em criação e atualização (snapshots antes/depois).
- **Epistemologia/segurança de domínio:** naturezas explícitas; `interpretado`/`a_confirmar` não tratados como fato; sem promoção automática; sem coleta/agentes/autoderivação; sem uso de `relationships`.
- **Integridade referencial:** FKs definidas na migração/ORM; **validação explícita de referências opcionais adicionada no serviço** (ver seção 3) para garantir comportamento consistente.
- **Arquivamento/exclusão:** suportado por estados rastreáveis (`cancelled`/`archived`) via atualização explícita; sem endpoint de hard-delete dedicado.
- **Compatibilidade:** Foundation/D1/D2 preservados; regressão da suíte completa verde.

### 2.3 Validações automatizadas e de migração (finais)
| Verificação | Comando/contexto | Resultado |
|---|---|---|
| Migração em DB temporário | `alembic upgrade head` (SQLite temp) | **OK** (cadeia até `b6c7d8e9f0a1`) |
| Estado migração DB local | `alembic -c backend/alembic.ini current` | **OK** — `b6c7d8e9f0a1 (head)` |
| Pytest completo | `PYTHONPATH=backend backend/.venv/bin/python -m pytest -q` | **OK** — **30 passed** |
| Ruff | `ruff check --no-cache backend/app backend/tests` | **OK** — All checks passed |
| Mypy | `mypy --config-file backend/pyproject.toml backend/app` | **OK** — Success (70 source files) |
| TypeScript | `npm run typecheck` (frontend) | **OK** |
| ESLint | `npm run lint` (frontend) | **OK** |
| Build frontend | `npm run build` (frontend) | **OK** — 1632 módulos |

## 3. Problemas encontrados

1. **Integridade de referências opcionais não validada explicitamente no serviço (corrigido).**  
   - **Descrição:** `create_interaction`/`update_interaction` aceitavam IDs opcionais (`document_id`, `research_source_id`, `raw_record_id`, `claim_id`, `evidence_id`) sem verificar existência prévia. Na validação assistida, uma referência inexistente retornou `201` no contexto de teste utilizado, indicando risco de inconsistência quando a aplicação efetiva de FKs não está garantida pelo contexto de conexão/ambiente.  
   - **Impacto potencial:** registros de interação com referências órfãs/inválidas e comportamento inconsistente entre ambientes.  
   - **Severidade:** média (integridade/consistência de dados; dentro do escopo D3).

2. **Validação manual de UI em navegador (resolvida por smoke test).**  
   - **Descrição:** executado smoke test em navegador (19/11/2026, Vite local + backend local, browser in-app) cobrindo navegação, resumo/timeline, naturezas/estados, detalhe com proveniência/referências e ações explícitas, sem erros de console e com endpoints 200.  
   - **Impacto:** aceite visual/funcional básico de UI comprovado em cenário controlado; automação E2E dedicada permanece opcional.

## 4. Correções realizadas e necessárias

### 4.1 Realizadas nesta revisão (working tree)
- **Validação explícita de referências opcionais (integridade):** adicionada `_validate_optional_refs` em `backend/app/knowledge/dossiers/history_service.py`, aplicada em criação e atualização, validando existência de `document_id`, `research_source_id`, `raw_record_id`, `claim_id` e `evidence_id` quando informados (retorno 404 para referência inexistente; string vazia normalizada para nulo). Atualização correspondente em `backend/tests/unit/test_dossiers_history.py` para exigir 404 em referência inválida. Regressão/validações reexecutadas com sucesso.
- **Documentação atualizada** para refletir o estado real de D3 (módulo e docs de projeto), incluindo regra de integridade de referências e status de validação/pendências:
  - `docs/modules/dossiers/DOSSIERS_SPECIFICATION.md`
  - `docs/modules/dossiers/DOSSIERS_DATA_MODEL.md`
  - `docs/modules/dossiers/DOSSIERS_API.md`
  - `docs/modules/dossiers/DOSSIERS_UI.md`
  - `docs/modules/dossiers/DOSSIERS_TEST_PLAN.md`
  - `docs/modules/dossiers/DOSSIERS_CHANGELOG.md`
  - `docs/DATA_MODEL.md`
  - `docs/API.md`
  - `docs/PROJECT_STATUS.md`
  - `docs/ROADMAP.md`

### 4.2 Necessárias adicionais
- **Nenhuma correção funcional adicional identificada** no escopo D3 com base nas inspeções e validações executadas (incluindo smoke test de UI em cenário controlado). Ajustes finos de UX podem ser considerados opcionalmente em evolução futura.

## 5. Pendências
- **Formalização:** alterações de D3 (código, testes, migração versionada, documentação e auditoria) **commitadas e publicadas** em `origin/main`, conforme autorização explícita desta etapa (sem D4/D5).
- **Banco local:** DB local migrado para head `b6c7d8e9f0a1` (gitignored) — consistente com o código em revisão; nenhum dado local apagado/sobrescrito.
- **Validação manual de navegador/UI:** smoke test concluído em 19/11/2026 (cenário local controlado). Automação E2E dedicada permanece opcional.
- **Fora de escopo (mantido pendente por autorização futura):** D4 Connections, D5 Strategic Insights, D6 consolidação; sem novas funcionalidades além de D3.

## 6. Estado do banco e da working tree
- **Alembic (local):** `b6c7d8e9f0a1 (head)` em `scout/backend/data/scout.db`.
- **Alembic (temp, verificado):** `upgrade head` concluído com sucesso até `b6c7d8e9f0a1`.
- **Git:** branch `main`, `HEAD/origin/main` em `0e3b05a`; **working tree não limpo** com modificações e arquivos não rastreados relativos a D3, correção de integridade, documentação atualizada e este relatório.
- **Commits/push desta etapa:** **realizados** (publicação de D3 em `origin/main`), mediante autorização explícita.

## 7. Resultado consolidado dos testes e checks
- **Pytest:** 30 passed (inclui Foundation, D1, D2, D3).
- **Ruff:** aprovado.
- **Mypy:** aprovado (70 arquivos).
- **Frontend typecheck / ESLint / build:** aprovados (build 1632 módulos).
- **Migrações:** aprovadas em DB temporário e head local verificado.
- **Validação funcional assistida D3 (API):** fluxos 1–8 atendidos conforme tabela da seção 2.1; referência opcional inválida rejeitada após correção (404).

## 8. Recomendação de aprovação ou reprovação de D3

**Recomendação: APROVAÇÃO para formalização e publicação de D3.**

**Fundamentos:**
- Implementação D3 alinhada ao plano e às restrições (determinística, local-first, rastreável, naturezas/estados explícitos, sem promoção automática a fato, sem D4/`relationships`, sem agentes/coleta/derivação automática, sem dependências pagas, compatível com Foundation/D1/D2).
- Validações automatizadas completas verdes (30 testes, lint/tipagem/build) e migrações consistentes (temp e local head `b6c7d8e9f0a1`).
- Fluxos funcionais D3 validados em nível de API/serviço; correção de integridade de referências opcionais identificada e aplicada com sucesso.

**Condições/ressalvas atendidas/observações:**
- **Smoke test de UI executado (19/11/2026):** navegação, resumo/timeline, naturezas/estados, detalhe com proveniência/referências e ações explícitas verificados com sucesso (sem erros de console, endpoints 200). Automação E2E dedicada permanece opcional.
- **Formalização autorizada e executada:** commit e push das alterações D3 + correção + documentação + este relatório, sem D4/D5 e sem alteração de escopo de Foundation/D1/D2.
