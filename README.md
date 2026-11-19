# SCOUT — Personal Strategic Intelligence System (Foundation V1.1)

Monólito modular **local-first** (uso exclusivamente local), com frontend e backend desacoplados, SQLite como fonte oficial e infraestrutura preparada para ingestão rastreável, controle humano e operação conservadora.

> **Fase atual:** Foundation V1.1 **concluída em escopo A–H** (validação e documentação consolidadas). Fase de runtime/API: `foundation-g`. **Não** implementa inteligência de domínio, previsões/simulações operacionais, funcionalidades completas dos 8 módulos de produto, execução automática de modelos de IA, nem integrações com APIs comerciais pagas.

## Princípios e restrições
- **Local-only:** serviços vinculados a loopback (`127.0.0.1`), sem exposição à internet. Conexões de saída apenas para fontes externas autorizadas/configuradas e serviços locais (ex.: Ollama em `127.0.0.1:11434`, verificação sob demanda), quando aplicável.
- **Dados locais:** SQLite em `backend/data/scout.db` (fonte oficial) e arquivos em `backend/data/` (gitignored).
- **Controle humano e rastreabilidade:** ações sensíveis sob controle do usuário; procedência e histórico preservados (`audit_events`, `processing_events`, `data_changes`); **inferências não são promovidas a fato automaticamente**.
- **Confiança:** conteúdo externo tratado como dado não confiável (nunca como instrução); validação de entradas/saídas e tratamento controlado de erros.
- **Desempenho (8 GB RAM):** execução controlada, sem paralelismo pesado, processamento sob demanda; scheduler conservador com estado canônico no banco (**desabilitado por padrão**).

## Stack (Foundation)
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand, Apache ECharts, Cytoscape.js (dependências base; módulos analíticos não implementados)
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, APScheduler, HTTPX
- **Dados:** SQLite, sistema de arquivos local
- **IA local (abstração):** Ollama (modelo de referência: Qwen3 4B), verificação sob demanda, **sem inferência automática** na Foundation

## Estrutura
- `frontend/` — SPA, App Shell/Design System, navegação das 8 áreas (placeholders), integração real de estado e monitoramento mínimo de ingestão em **System**
- `backend/` — API FastAPI, camadas/modularização, modelos e migrações, ingestão (Source Registry, conector `rss_atom`, pipeline/scheduler mínimo) e rastreabilidade
- `docs/` — documentação consolidada (9 documentos)

## Execução local

### Pré-requisitos
- Python 3.9+ com `venv` e `pip` (ambiente validado: 3.9.6)
- Node.js e npm (ambiente validado: Node v26.5.0, npm 11.17.0)

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # opcional
.venv/bin/alembic upgrade head   # prepara backend/data/scout.db (migração 426757a848bb)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API: `http://127.0.0.1:8000`
- Health: `GET /api/v1/health` (fase `foundation-g`)
- OpenAPI: `http://127.0.0.1:8000/docs`

### Frontend
```bash
cd frontend
npm install
cp .env.example .env             # opcional
npm run dev
```
- App: `http://127.0.0.1:5173` (proxy `/api` → `http://127.0.0.1:8000`)

## Verificações
```bash
# Backend
cd backend
.venv/bin/ruff check app tests
.venv/bin/mypy app
.venv/bin/python -m pytest -q

# Frontend
cd frontend
npm run typecheck
npm run lint
npm run build
```

> **Nota:** a suíte de testes backend inclui operações HTTP reais de leitura (somente metadados/títulos, limites conservadores) contra o recurso de referência da **Decisão 4** confirmado: `https://www.w3.org/news/feed/` (W3C News, feed público, autorizado para continuidade nos limites atuais; substituição futura requer autorização explícita).

## Decisão 4 (confirmada)
- **Conector/fonte de referência (`rss_atom`):** confirmado e autorizado pelo usuário o recurso público `https://www.w3.org/news/feed/` (RSS, W3C News) para testes/leitura/coleta real local de referência.
- **Restrições mantidas:** somente leitura, metadados/títulos/links/ids/datas, **máx. 5 itens**, timeouts e limites de tamanho; sem preservação de corpo/conteúdo completo no pipeline padrão (preservação condicional apenas quando explicitamente permitida por configuração/permissões/licença). Substituição futura requer nova autorização explícita.

## Estado
- **A–H:** concluídos no escopo da Foundation V1.1 (infraestrutura, schema/migração, UI base/integração, Source Registry/conector real, pipeline/scheduler mínimo rastreável, monitoramento operacional mínimo em System, validações e documentação).
- **Módulos funcionais (Radar, Dossiers, Knowledge Graph, Predictions, Scenario Lab, Action Center, Agent Control, System completo):** não implementados (placeholders/navegação, sem simulação).
- Consulte `docs/PROJECT_STATUS.md` e os demais documentos em `docs/` para detalhes, contratos, limitações e riscos.
