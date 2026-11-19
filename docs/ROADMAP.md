# ROADMAP — SCOUT (Foundation V1.1)

> **Status:** Foundation V1.1 (A–H) **concluída no escopo definido e validada**. Evolução pós-Foundation sujeita a aprovação.

## Subetapas da Foundation
- **A. Estrutura e ambiente local** — **concluída:** monorepo, esqueleto backend/frontend, tooling, loopback, docs base.
- **B. Backend e banco de dados** — **concluída:** 15 entidades ORM, Alembic/migração inicial (`426757a848bb`), storage local, endpoints base/estado.
- **C. Frontend e Design System** — **concluída:** tokens/temas, App Shell responsivo, navegação/estados/acessibilidade básica.
- **D. Integração frontend-backend** — **concluída:** consumo tipado de `health/system/info/db/status` com tratamento de estados.
- **E. Source Registry e conectores** — **concluída:** CRUD/ativação de fontes, conectores plugáveis, conector real `rss_atom`, teste de conexão real e rastreabilidade mínima (Decisão 4 auto-aplicada, confirmar/substituir).
- **F. Scheduler e pipeline básico** — **concluída:** APScheduler conservador com estado canônico no banco e reidratação controlada, `collection_jobs/runs`, coleta real rastreável, normalização/validação/deduplicação básica, persistência condicional de original, eventos/alterações e endpoints de status/histórico.
- **G. Source Manager e monitoramento** — **concluída:** visão em System (UI) de conectores/fontes/jobs/runs/eventos e auditoria recente com controles mínimos reais (teste/criação/execução), estados e contratos do backend (sem simulações).
- **H. Testes, documentação e validação** — **concluída:** consolidação dos 9 docs, verificações finais backend/frontend, correções de consistência e relatório de validação (limitações/decisões pendentes registradas).

## Decisão pendente (transversal)
- **Decisão 4:** confirmar permanência do recurso de referência `https://www.w3.org/news/feed/` ou substituí-lo por RSS/Atom/HTTP GET explicitamente autorizado.

## Pós-Foundation (não iniciado, sujeito a aprovação)
- Evolução de ingestão/domínio: `documents`, extração/claims/evidências/entidades/relacionamentos, monitoramento e controles operacionais avançados.
- Módulos funcionais: Radar, Dossiers, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control, System completo.
- Inteligência de domínio e capacidades preditivas/simulações, sempre com controle humano, rastreabilidade e restrições de segurança/performance preservadas.
