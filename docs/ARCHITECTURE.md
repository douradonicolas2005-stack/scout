# ARCHITECTURE — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H (arquitetura implementada e validada para Foundation A–G).

## Estilo
Monólito modular, **local-first**, com frontend e backend desacoplados. Serviços locais em loopback (`127.0.0.1`), sem exposição externa.

## Camadas
- **Application:** React+TS+Vite (Tailwind/shadcn/Zustand), API FastAPI, validação Pydantic/TS. Área **System** expõe estado da plataforma e Source Manager/monitoramento mínimo (conectores/fontes/jobs/runs/eventos/auditoria) com controles reais suportados pelo backend.
- **Knowledge:** SQLite (SQLAlchemy 2.0 + Alembic), 15 entidades de domínio/fontes/ingestão/rastreabilidade, arquivos locais (`data/raw`, `data/documents`).
- **Intelligence:** abstração de LLM (Ollama, Qwen3 4B referência) sob demanda, interfaces de orquestração/agentes (sem inferência automática na Foundation).
- **Predictive:** interfaces/stubs para estatística, séries temporais e simulações (não operacional).
- **Ingestion:** Source Registry, conectores plugáveis, scheduler conservador com estado canônico no banco, normalização/validação/deduplicação e pipeline rastreável mínimo.
- **Control:** aprovações, permissões, auditoria e histórico de ações (base implementada; controles operacionais ampliados fora do escopo atual).

## Comunicação
- HTTP/JSON versionado em `/api/v1`, OpenAPI em `/docs`.
- Frontend (5173) → proxy `/api` → Backend (8000), ambos loopback; CORS restrito a origens locais.

## Armazenamento local
- DB: `backend/data/scout.db` (WAL/foreign_keys/busy_timeout na configuração de execução).
- Arquivos: `backend/data/raw/`, `backend/data/documents/` (gitignored). Preservação de conteúdo bruto condicionada a configuração/permissões/licença.

## Decisões base e estado atual
- **Dados/modelagem:** SQLAlchemy 2.0 + Pydantic (schemas separados); SQLite fonte única; Alembic para migrações (revisão `426757a848bb`, sem novas migrações em E/F/G).
- **Scheduler/pipeline:** APScheduler (Background, conservador), estado/agendamento canônico no banco (`collection_jobs`), dispatch por tick, reidratação controlada quando habilitado, **desabilitado por padrão**, sem paralelismo pesado. Pipeline mínimo operacional com coleta real (`rss_atom`), validação/deduplicação, `raw_records`, `processing_events`, `data_changes`, retries conservadores.
- **IA local:** Ollama como abstração + configuração + verificação de disponibilidade sob demanda; **sem inferência automática** e sem promoção automática de inferência a fato.
- **Ingestão/UI operacional:** Source Registry/conectores plugáveis, teste real de conexão/leitura mínima e monitoramento/controles mínimos em **System** consumindo contratos reais (sem simulações).
- **Decisão 4 (confirmada):** recurso público de referência autorizado `https://www.w3.org/news/feed/` (RSS, W3C News) para testes/coleta real local (metadados/títulos, máx. 5 itens, read-only, timeouts/limites conservadores), conforme confirmação explícita do usuário; substituição futura requer nova autorização.

## Limites da Foundation
As 8 áreas de produto (além da visão/monitoramento mínimo em System) permanecem sem implementação funcional de domínio/inteligência/predição/simulação; evolução para `documents`/claims/evidências/entidades/relacionamentos e controles avançados depende de etapas aprovadas.
