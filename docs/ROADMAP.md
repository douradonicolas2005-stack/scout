# ROADMAP — SCOUT (Foundation V1.1)

> **Status:** Foundation V1.1 (A–H) **concluída e validada**. Dossiers D1–D2 entregues; **D3 implementado, validado (incluindo smoke test de UI) e publicado**. Evoluções D4+ sujeitas a planejamento técnico aprovado e autorização explícita.

## Subetapas da Foundation
- **A. Estrutura e ambiente local** — **concluída.**
- **B. Backend e banco de dados** — **concluída** (15 entidades ORM, migração `426757a848bb`).
- **C. Frontend e Design System** — **concluída.**
- **D. Integração frontend-backend** — **concluída.**
- **E. Source Registry e conectores** — **concluída** (`rss_atom`, Decisão 4 confirmada: `https://www.w3.org/news/feed/`).
- **F. Scheduler e pipeline básico** — **concluída** (APScheduler conservador, DB-canonical).
- **G. Source Manager e monitoramento** — **concluída** (System UI, controles mínimos).
- **H. Testes, documentação e validação** — **concluída.**

## Dossiers V1.0 (incremental, pós-Foundation)
- **D1 — Entity Profiles (concluída, entregue):** perfis, CRUD/pesquisa/filtros, duplicidades sugeridas sem fusão, UI home e página da entidade, migração `b7d1e2f3a4c5`, testes e docs.
- **D2 — Research & Evidence (concluída, entregue):** fontes de pesquisa, documentos/referências, afirmações (epistemologia), evidências e conflitos com proveniência/rastreabilidade e Research Workspace determinístico; migrações `c1d2e3f4a5b6`→`a5b6c7d8e9f0`.
- **D3 — Relationship History (concluída, publicada):** interações e linha do tempo por entidade com natureza explícita (`declarado/observado/interpretado/a_confirmar`), estados/proveniência opcional e rastreabilidade; migração `b6c7d8e9f0a1`, serviço/API/UI/testes, documentação e smoke test de UI concluídos. Não utiliza `relationships` (reservado a D4).
- **D4 — Connections (pendente, requer autorização):** relações entre entidades com temporalidade/evidências e visualização simplificada (uso de `relationships`).
- **D5 — Strategic Insights (pendente):** hipóteses/oportunidades fundamentadas, sem execução automática.
- **D6 — Consolidação (pendente):** refinamento e integração do módulo.

## Demais evoluções (não iniciadas, sujeitas a aprovação)
- Evolução de ingestão/domínio: `documents` derivados, extração/claims/evidências/encaminhamento completo; monitoramento e controles operacionais avançados.
- Módulos funcionais: Radar, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control, System completo.
- Inteligência de domínio e capacidades preditivas/simulações, sempre com controle humano, rastreabilidade e restrições de segurança/performance preservadas.
