# ROADMAP — SCOUT (Foundation V1.1)

> **Status:** Foundation V1.1 (A–H) **concluída no escopo definido e validada**. Evolução pós-Foundation sujeita a aprovação.

## Subetapas da Foundation
- **A. Estrutura e ambiente local** — **concluída:** monorepo, esqueleto backend/frontend, tooling, loopback, docs base.
- **B. Backend e banco de dados** — **concluída:** 15 entidades ORM, Alembic/migração inicial (`426757a848bb`), storage local, endpoints base/estado.
- **C. Frontend e Design System** — **concluída:** tokens/temas, App Shell responsivo, navegação/estados/acessibilidade básica.
- **D. Integração frontend-backend** — **concluída:** consumo tipado de `health/system/info/db/status` com tratamento de estados.
- **E. Source Registry e conectores** — **concluída:** CRUD/ativação de fontes, conectores plugáveis, conector real `rss_atom`, teste de conexão real e rastreabilidade mínima (Decisão 4 confirmada: `https://www.w3.org/news/feed/`).
- **F. Scheduler e pipeline básico** — **concluída:** APScheduler conservador com estado canônico no banco e reidratação controlada, `collection_jobs/runs`, coleta real rastreável, normalização/validação/deduplicação básica, persistência condicional de original, eventos/alterações e endpoints de status/histórico.
- **G. Source Manager e monitoramento** — **concluída:** visão em System (UI) de conectores/fontes/jobs/runs/eventos e auditoria recente com controles mínimos reais (teste/criação/execução), estados e contratos do backend (sem simulações).
- **H. Testes, documentação e validação** — **concluída:** consolidação dos 9 docs, verificações finais backend/frontend, correções de consistência e relatório de validação (limitações/decisões pendentes registradas).

## Decisão 4 (confirmada)
- **Recurso de referência autorizado:** `https://www.w3.org/news/feed/` (RSS, público, W3C News), confirmado pelo usuário para continuidade como fonte/conector de referência em testes/coleta real local, com limites conservadores (read-only, metadados/títulos, máx. 5 itens, timeouts/tamanho). Substituição futura requer autorização explícita.

## Dossiers V1.0 (incremental, pós-Foundation)
- **D1 — Entity Profiles (concluída, autorizada):** perfis/cadastro/edição/pesquisa/consulta/detecção de duplicidades (sem fusão), UI home e página da entidade (seções futuras sem simulação), migração aditiva `b7d1e2f3a4c5`, testes e docs em `docs/modules/dossiers/`.
- **D2 — Research & Evidence (concluída, autorizada, implementada no working tree):** fontes de pesquisa, documentos/referências, afirmações (classificação epistemológica), evidências e conflitos com proveniência/rastreabilidade e Research Workspace determinístico (manual-first, sem promoção automática a fato). Migrações aditivas `c1d2e3f4a5b6`→`a5b6c7d8e9f0` (validadas em DB temporário; aplicação no DB local pendente de autorização), API/UI/testes/docs atualizados.
- **D3 — Relationship History (pendente):** interações e linha do tempo (declarado/observado/interpretado/a confirmar).
- **D4 — Connections (pendente):** relações entre entidades com temporalidade/evidências e visualização simplificada.
- **D5 — Strategic Insights (pendente):** hipóteses/oportunidades fundamentadas, sem execução automática.
- **D6 — Consolidação (pendente):** refinamento e integração do módulo.

## Demais evoluções (não iniciadas, sujeitas a aprovação)
- Evolução de ingestão/domínio: `documents`, extração/claims/evidências/encaminhamento completo; monitoramento e controles operacionais avançados.
- Módulos funcionais: Radar, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control, System completo.
- Inteligência de domínio e capacidades preditivas/simulações, sempre com controle humano, rastreabilidade e restrições de segurança/performance preservadas.
