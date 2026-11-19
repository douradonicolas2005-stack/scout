# VISION — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H (visão e princípios alinhados ao estado validado da Foundation V1.1).

## Visão
SCOUT é um Personal Strategic Intelligence System **local-first** para consolidar informações de fontes autorizadas, organizar conhecimento com rastreabilidade e apoiar decisões sob controle humano.

## Objetivo da Foundation V1.1
- Estabelecer infraestrutura local confiável, modular e rastreável (aplicação, conhecimento, ingestão, controle; inteligência/preditiva como interfaces).
- Garantir execução em loopback, SQLite como fonte oficial, persistência local e observabilidade operacional mínima.
- Preparar expansão incremental dos módulos sem simular funcionalidades.

## Estado alcançado (A–H)
- Monorepo backend/frontend local, App Shell e Design System, navegação das 8 áreas como placeholders.
- SQLite + SQLAlchemy 2.0 + Alembic (15 entidades), storage local e endpoints de estado.
- Source Registry, conectores plugáveis e conector de referência real (`rss_atom`) com controles conservadores.
- Pipeline mínimo rastreável de coleta (`collection_jobs/runs`, `raw_records`, eventos/alterações) e scheduler APScheduler com estado canônico no banco (desabilitado por padrão, sem paralelismo pesado).
- Source Manager/monitoramento mínimo em **System** (conectores/fontes/jobs/runs/eventos/auditoria, controles reais suportados) e validações consolidadas.

## Princípios
- **Local-only** e controle humano sobre ações sensíveis.
- **Procedência, versionamento e auditoria** em primeiro lugar.
- **Semântica explícita:** fato verificado, declaração, inferência, hipótese, previsão, desconhecido — **sem promoção automática de inferência a fato**.
- **Confiança:** conteúdo externo tratado como dado não confiável (nunca como instrução).
- **Desempenho consciente** em 8 GB de RAM; execução controlada e sem dependências pagas obrigatórias.

## Fora de escopo (Foundation)
Inteligência de domínio, previsões/simulações operacionais, funcionalidades completas dos 8 módulos, extração/claims/evidências/entidades/relacionamentos completos, execução automática de modelos de IA, KuzuDB/bancos vetoriais/Redis/filas pesadas, integrações pagas.
