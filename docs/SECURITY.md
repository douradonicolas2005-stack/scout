# SECURITY — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H (controles implementados e validados em A–G).

## Superfície e rede
- Serviços vinculados a `127.0.0.1` (backend/frontend); sem exposição à internet.
- Conexões de saída apenas para fontes autorizadas/configuradas e serviços locais (ex.: Ollama em loopback, verificação sob demanda). Testes de conexão e coletas do pipeline usam conectores configurados (recurso de referência atual auto-aplicado: `https://www.w3.org/news/feed/`, ver Decisão 4 em `INGESTION_ARCHITECTURE.md`) com HTTP read-only, timeouts e limites conservadores (incl. máx. de itens/tamanho).

## Segredos e dados
- Credenciais fora do código-fonte (`.env` gitignored). Fontes armazenam referências de autenticação (`auth_method`, `auth_credential_ref`) e não segredos em claro.
- Separação entre dados públicos e confidenciais; dados/arquivos locais em `backend/data/` (gitignored).
- **Preservação condicional:** armazenamento de conteúdo bruto em `backend/data/raw/<source_id>/` ocorre somente quando permitido por configuração/permissões/licença (`config_json.preserve_raw` ou `permissions_json.allow_storage/preserve_raw`); caso contrário, persistem-se apenas metadados/registros necessários ao pipeline mínimo.

## Confiança e validação
- Conteúdo externo tratado como **dado não confiável**, nunca como instrução (proteção contra prompt injection). Parsing limitado a metadados necessários.
- Validação de entradas/saídas (Pydantic/FastAPI). Conectores validam configuração (URL `http/https`, limites de itens/timeout/tamanho) e tratam erros de rede/parse de forma controlada.
- Pipeline aplica validação básica e deduplicação antes da persistência; falhas são registradas sem promoção automática de inferência a fato.

## Controle e auditoria
- `audit_events` registram operações relevantes (ex.: criação/atualização/teste de fontes, criação de jobs). `processing_events` registram testes de conexão e estágios/resultado de jobs/runs; `data_changes` registram alterações persistidas (ex.: criação de `raw_records`).
- Scheduler (APScheduler) opera em modo conservador, com estado canônico no banco, reidratação controlada e sem paralelismo pesado; **desabilitado por padrão**. Execuções manuais e agendadas permanecem rastreáveis.
- UI de monitoramento/controles mínimos (**System**) opera sobre contratos reais locais (teste/criação/execução de jobs, leitura de histórico/eventos/auditoria), sem simular operações nem executar inferência automática.
- Ações sensíveis sob controle humano; nenhuma ação externa não autorizada nem envio de dados confidenciais a IA externa. Respeito a condições de acesso e licenciamento das fontes.

## Limitações conhecidas
- Confirmação/substituição pendente do recurso de referência da Decisão 4 para continuidade operacional.
- Controles operacionais avançados, políticas de retenção/gestão de credenciais e hardening adicional são escopo de etapas futuras aprovadas.
