# SCOUT — Planejamento Técnico D2: Research & Evidence

> **Módulo:** Dossiers V1.0 · **Subetapa:** D2 — Research & Evidence · **Status do documento:** planejamento técnico (sem implementação) · **Data:** 19/11/2026 · **Base de análise:** código e documentação reais do repositório em `main@865018a` com D1 implementado/validado no working tree (não commitado), Foundation V1.1 (A–H) consolidada.
>
> **Princípio central (normativo):** toda informação relevante deve possuir origem identificável, contexto, estado de verificação e relação clara com a entidade correspondente. Informação registrada não é automaticamente verdadeira; inferências não são promovidas a fato sem fluxo explícito e revisão humana.

## 1. Diagnóstico da estrutura atual

### 1.1 Estado funcional e documental
- **Foundation V1.1 (A–H):** infraestrutura local-first, App Shell, API v1, SQLite/Alembic, Source Registry/conector `rss_atom`, pipeline mínimo de coleta rastreável (jobs/runs/raw_records/eventos/alterações) e monitoramento mínimo em System. Runtime/API `phase=foundation-g` (`docs/PROJECT_STATUS.md`, `docs/ARCHITECTURE.md`).
- **Dossiers D1 — Entity Profiles (concluída, não commitada):** perfis de entidade persistentes e consultáveis com CRUD/pesquisa/filtros, identificadores e aliases auxiliares, sugestão determinística de duplicidades (sem fusão), rastreabilidade por `audit_events` e `data_changes`, UI home e página da entidade (`/dossiers`, `/dossiers/:entityId`). Seções futuras — **Histórico (D3), Relações (D4), Evidências e documentos (D2), Insights (D5)** — já existem na UI como placeholders explícitos sem simulação (`frontend/src/pages/DossierEntityPage.tsx`).
- **Documentação do módulo:** `docs/modules/dossiers/{DOSSIERS_SPECIFICATION,DATA_MODEL,API,UI,TEST_PLAN,CHANGELOG}.md` refletem D1 entregue e D2–D6 pendentes.

### 1.2 Estruturas de dados existentes (inspeção real)

| Estrutura | Estado real | Uso atual | Observações para D2 |
|---|---|---|---|
| `entities` (estendida D1, migração `b7d1e2f3a4c5`) | Canônica, com `description/profile_status/primary_location/profile_data`, verificação/confiança/proveniência temporal e `source_first_id` | Perfis D1 | Base obrigatória de vínculo para documentos/afirmações/evidências por entidade; **reutilizar sem recriar**. |
| `entity_identifiers`, `entity_aliases` (D1) | Tabelas auxiliares com FKs CASCADE para `entities` | Busca/deduplicação D1 | Sem impacto estrutural direto em D2; manter compatibilidade. |
| `sources` (Foundation, `426757a848bb`) | Cadastro operacional de **fontes de ingestão/coleta**: `resource_locator`, `connection_type`, auth refs, frequência/agendamento, status/ativo, `config_json`, `permissions_json`, `terms_conditions` | Source Registry, validação por conector, testes de conexão, jobs/coleta | Semântica orientada a coleta automatizada/configurada. **Não é equivalente** a “fonte de pesquisa/referência” do dossiê (consulta manual, confiabilidade justificada por contexto de pesquisa, classificação bibliográfica). Reuso direto exigiria sobrecarga semântica e campos obrigatórios inadequados. |
| `raw_records` (Foundation) | Registros brutos coletados com proveniência (`source_id`, `run_id`, `external_id`, `content_hash`, `storage_path`, `is_preserved`, metadados, datas, `verification_status`) e índices de deduplicação | Pipeline de ingestão mínimo (F) | Excelente âncora de proveniência para documentos/afirmações derivados de coleta; **reutilizar por referência** (sem duplicar metadados de coleta). `storage_path` aponta para `backend/data/raw/<source_id>/` quando preservado. |
| `documents` (Foundation) | Tabela mínima: `id`, `source_id` (**NOT NULL**, FK CASCADE), `raw_record_id` (SET NULL), `title`, `mime_type`, `storage_path`, `checksum`, `size_bytes`, `language`, `published_at`, `collected_at` (default), `metadata_json`; **sem** `created_at/updated_at`, **sem** descrição/tipo/origem rica, **sem** data de captura/ocorrência distinta, **sem** classificação/acesso, **sem** vínculo a entidade(s) | Definida no schema, **não populada** pelo pipeline mínimo | Reutilizável como base de artefato documental, mas **insuficiente** para o escopo D2 (associação a entidades, metadados completos, integridade/controle, cadastro manual sem fonte de ingestão obrigatória, múltiplas origens/proveniências). Requer extensão aditiva cuidadosa e/ou estruturas complementares. |
| `extracted_claims` (Foundation) | `claim_text`, `structured_json`, `claim_type` (default `declaracao`), `confidence`, `verification_status` (default `nao_verificado`), `version`, `supersedes_claim_id`, vínculos `source_id` (**NOT NULL**)/`raw_record_id`/`document_id`, datas procedência/validade, `TimestampMixin` | Definida, **não populada** | Boa base semântica parcial (`claim_type`, verificação, versionamento/supersessão, temporalidade), mas falta: **vínculo explícito à entidade**, justificativa da confiança/verificação, origem de registro (manual/extraído), suporte a conflitos/contradições como relação rastreável, e flexibilidade para afirmações inseridas manualmente sem `source_id` de ingestão obrigatório. |
| `evidence` (Foundation) | `claim_id` (NOT NULL), `source_id` (NOT NULL), `raw_record_id`, `locator`, `snippet`, `note`, `published_at`, `collected_at`, `confidence`, `verification_status`, `created_at` (sem `updated_at`) | Definida, **não populada** | Suporta ligação claim↔proveniência textual básica, mas falta: `document_id`, **tipo de evidência**, **relação de suporte/contestação/contextualização**, localização precisa estruturada, e flexibilidade para vincular documento/fonte de pesquisa sem depender exclusivamente de `sources` de ingestão. |
| `relationships` (Foundation) | Relações entidade↔entidade com tipo, atributos, `claim_id`/`evidence_id`, confiança/verificação/temporalidade | Definida, **não utilizada** (prevista D4) | Não criar estruturas paralelas para “conflitos entre afirmações”; avaliar uso/ligação futura com cuidado, mas **D4 permanece fora de escopo**. Conflitos D2 devem ser modelados no domínio de claims/evidências. |
| `data_changes` | Histórico genérico (`entity_table`, `entity_id`, before/after, razão, `run_id`, ator) | Usado por D1 e pipeline | **Reutilizar** para rastreabilidade de mutações D2 (fontes de pesquisa, documentos, afirmações, evidências, vínculos). |
| `processing_events` | Eventos por estágio/status/mensagem/payload/duração | Ingestão e testes de conexão | **Reutilizar** para eventos determinísticos de D2 (registro/importação/validação/hash/associação), sem pipeline pesado. |
| `audit_events` | Auditoria de ações/ator/alvo/severidade/detalhes/origem | D1, ingestão, sistema | **Reutilizar** para ações de criação/atualização/associação/verificação D2. |
| `agent_runs` | Registro de execuções de agentes/LLM | Definido, não utilizado | Manter inalterado; apenas referência futura (Ollama assistido opcional, fora de D2). |

Enums/valores existentes relevantes (`app/knowledge/provenance.py`): `ClaimType` (`fato_verificado`, `declaracao`, `inferencia`, `hipotese`, `previsao`, `desconhecido`) e `VerificationStatus` (`nao_verificado`, `em_verificacao`, `verificado`, `contestado`, `invalido`).

### 1.3 Implementação real relacionada (serviços, API, ingestão, UI)
- **API/roteamento:** `backend/app/api/router.py` inclui `dossiers` em `/api/v1`; endpoints D1 em `backend/app/api/v1/endpoints/dossiers.py`; schemas em `backend/app/api/v1/schemas/dossiers.py`.
- **Serviço D1:** `backend/app/knowledge/dossiers/service.py` centraliza normalização, snapshots, `record_audit`/`record_data_change`, CRUD e duplicidades — padrão a ser estendido de forma coesa (possível modularização interna em `knowledge/dossiers/` sem quebrar D1).
- **Ingestão:** `backend/app/ingestion/collection.py` cria jobs/runs, coleta via conectores, normaliza/valida/deduplica e persiste **`raw_records`**; atualização de `sources.last_collected_at`; preservação condicional em `backend/data/raw/<source_id>/`. **Não** cria `documents`, `extracted_claims`, `evidence` nem vínculos com entidades. Config/storage: `backend/app/core/config.py` define `data_dir/raw_data_dir/documents_dir` (`backend/data/documents/` existe como diretório-alvo, gitignored).
- **Frontend:** `frontend/src/lib/api/{client.ts,types.ts}` com operações D1; `frontend/src/pages/DossiersPage.tsx` e `frontend/src/pages/DossierEntityPage.tsx` com estados e placeholders; navegação preserva App Shell (`frontend/src/app/App.tsx`, `routes.tsx`).
- **Testes:** suíte Foundation + D1 usa DB temporário com Alembic e, no estado atual, inclui acessos HTTP reais de leitura ao feed W3C em testes pré-existentes (ponto de atenção para política offline/determinística da suíte padrão em D2).

### 1.4 Lacunas principais para D2
1. **Modelo de “fonte de pesquisa” de dossiê** (primeira classe, manual/consultada) não existe com semântica adequada; `sources` de ingestão é conceitualmente distinto.
2. **`documents`** carece de metadados, tipagem, temporalidade completa, integridade/controle de acesso e, sobretudo, **associação explícita com entidades** e suporte a cadastro manual independente de `sources.id` de ingestão.
3. **`extracted_claims`** carece de **vínculo à entidade**, justificativa, origem do registro, flexibilidade para entrada manual e mecanismo explícito de **contradição/conflito**.
4. **`evidence`** carece de vínculo a documento/fonte de pesquisa, tipo e papel (suporta/contesta/contextualiza) e localização precisa estruturada.
5. **Vínculos N:N** necessários (documento↔entidade, claim↔entidade quando aplicável, evidência↔fontes/documentos múltiplos conforme caso) não estão modelados.
6. **API/UI de Research Workspace** inexistentes; não há contratos, serviços, upload/registro seguro de arquivos nem visualização de conflitos/pendências.
7. **Pipeline determinístico/manual** de registro (hash, deduplicação, validação, associação) e políticas de armazenamento/licença/permissão para documentos de dossiê precisam ser definidos sem acoplar ingestão pesada.

### 1.5 Restrições e premissas confirmadas
- Local-first, SQLite/Alembic aditivo, sem dependências novas, sem serviços externos pagos, sem inferência automática promovida a fato, sem coleta indiscriminada, sem paralelismo pesado, sem agentes autônomos.
- Primeira implementação D2: **determinística e com inserção manual prioritária**; Ollama/Qwen3 apenas possibilidade futura assistida com revisão humana (não implementar).
- Compatibilidade com D1/Foundation e integridade dos dados existentes obrigatórias.
- Este documento é o único artefato autorizado nesta etapa de planejamento (sem alterações de código/migrações/banco/commits).

## 2. Arquitetura proposta

### 2.1 Abordagem geral
- **Extensão aditiva e incremental** do módulo Dossiers dentro do monólito modular existente, preservando o App Shell e o Design System.
- **Reuso prioritário** de tabelas transversais (`audit_events`, `data_changes`, `processing_events`) e de estruturas de proveniência já presentes (`raw_records`, e opcionalmente `sources` de ingestão/documentos derivados) **por referência**, sem duplicar semântica operacional de ingestão.
- **Separação semântica clara:**
  - *Ingestion Source* (`sources`): configuração operacional de coleta (já existente).
  - *Research Source* (D2): fonte consultada/referenciada no contexto de pesquisa do dossiê (manual ou vinculada a proveniência de coleta), com confiabilidade/consulta/verificação próprias.
  - *Document*: artefato/informação documental associado a entidades e proveniências.
  - *Claim*: afirmação registrável (manual ou extraída de forma determinística/assistida futura), sempre vinculável a entidade e com estado epistemológico explícito.
  - *Evidence*: elemento rastreável que suporta/contesta/contextualiza uma afirmação com localização e origem.

### 2.2 Camadas e componentes (alinhados à arquitetura atual)

| Camada | Responsabilidade D2 | Componentes propostos (planejados) |
|---|---|---|
| **Knowledge (modelo/persistência)** | Representar fontes de pesquisa, documentos, vínculos entidade-documento, afirmações, conflitos e evidências com proveniência/temporalidade/verificação | Modelos ORM aditivos/extensões em `app/knowledge/models/domain.py` (ou organização equivalente) + migração Alembic aditiva; reuso de `data_changes`/`audit_events`/`processing_events`. |
| **Application/Serviço de domínio** | Regras determinísticas: validação, normalização, hash/deduplicação, associações, snapshots, registro de rastreabilidade, cálculo/derivação de estados de conflito e pendências | Evolução de `app/knowledge/dossiers/service.py` (ou decomposição em submódulos `research_sources.py`, `documents.py`, `claims.py`, `evidence.py` preservando API interna estável) com transações e checagens de integridade. |
| **API (FastAPI/Pydantic)** | Contratos explícitos para CRUD/consulta/associação/filtros, paginação, estados de erro e validações | Novos schemas Pydantic e endpoints sob `/api/v1/dossiers` (ou sub-rotas dedicadas), mantendo convenções D1 (`from_attributes`, validação 422, 404, conflitos 409 quando aplicável). |
| **Armazenamento local de arquivos** | Guardar artefatos documentais de forma controlada e verificável | Uso de `settings.documents_dir` (`backend/data/documents/`) com organização determinística por entidade ou por documento (hash/id), metadados de integridade (`checksum`, tamanho, mime), registro de `storage_path` relativo/absoluto controlado; **sem** exposição remota. Escrita somente quando permitido (config/permissão/licença/ação explícita). |
| **Frontend (Application UI)** | Research Workspace integrado ao dossiê: consulta objetiva, estados claros, formulários manuais e navegação por seções | Evolução de `DossierEntityPage` (seção Evidências e documentos D2) e componentes dedicados em `frontend/src/components/dossiers/research/` (ou equivalente), cliente/tipos API estendidos, preservação de App Shell/Design System e acessibilidade básica. |
| **Control/Observabilidade** | Auditoria e histórico de ações | `audit_events` para ações de usuário/sistema local; `data_changes` para mutações de domínio; `processing_events` para etapas determinísticas (ex.: validação/importação/hash/associação). |

### 2.3 Princípios de design específicos D2
- **Proveniência em primeiro nível:** todo claim e todo documento exibido deve expor origem (fonte de pesquisa e/ou fonte de ingestão/raw_record), contexto temporal e referências localizáveis.
- **Epistemologia explícita:** `claim_type` + `verification_status` + confiança + justificativa + origem do registro; UI deve rotular claramente (fato verificado, declaração, inferência, hipótese, previsão, desconhecido; pendente/em verificação/verificado/contestado/inválido).
- **Sem promoção automática:** transições para estados “verificado/fato” exigem ação explícita (registro/atualização manual com justificativa) — nunca inferência automática.
- **Determinismo:** extração/classificação assistida por IA, agentes e coletas externas **fora** da D2; cadastros e associações manuais/validações determinísticas **dentro**.
- **Minimização e controle:** armazenar apenas o necessário; respeitar licenças/permissões; permitir referência externa sem cópia local quando cópia não for permitida.
- **Conflitos como informação rastreável:** contradições registradas explicitamente (relação entre claims), com status e justificativa, sem resolução automática.

### 2.4 Fluxos conceituais (determinísticos)

1. **Registro de fonte de pesquisa:** usuário cadastra fonte (nome, tipo, domínio/URL, descrição, classificação, confiabilidade/justificativa, datas de consulta/verificação) → validação → persistência → auditoria/alteração.
2. **Registro de documento:** usuário informa metadados e origem (upload/arquivo local referenciado e/ou referência externa) e associa a uma ou mais entidades e fontes de pesquisa → cálculo de hash/checksum e verificação de duplicidade → persistência condicionada a permissão/licença → vínculo entidade-documento → auditoria/eventos.
3. **Registro de afirmação (claim):** usuário registra texto, entidade(s) relacionada(s), classificação epistemológica, datas, estado/confiança/justificativa e, quando houver, origem (documento/fonte/raw_record) → persistência → possibilidade de marcar conflito com outra afirmação.
4. **Registro de evidência:** usuário associa evidência à afirmação com trecho/localização precisa, tipo e papel (suporta/contesta/contextualiza), vinculando documento e/ou fonte de pesquisa/raw_record → persistência rastreável.
5. **Consulta (Research Workspace):** leitura agregada por entidade com filtros e indicadores de pendências/conflitos (derivados de dados persistidos), sem inferência automática.

### 2.5 Limites explícitos (fora da arquitetura D2)
- Sem agentes autônomos, sem crawling/coleta indiscriminada, sem integração obrigatória com APIs comerciais, sem processamento paralelo pesado.
- Sem implementação de D3 (timeline de interações), D4 (grafo de conexões entre entidades) ou D5 (insights estratégicos).
- Sem pipeline automático de extração de claims/evidências a partir de documentos na primeira implementação (apenas estrutura e inserção/associação manual determinística).

## 3. Modelo de dados detalhado

> Convenções: UUID string (36) como PK (padrão existente), `DateTime(timezone=True)` para instantes, JSON para metadados extensíveis controlados, FKs explícitas, índices para consultas por entidade/estado/data, defaults conservadores (`nao_verificado`, sem confiança implícita).

### 3.1 Reuso direto (sem alteração estrutural prevista)

| Tabela | Uso em D2 |
|---|---|
| `entities` | Alvo principal de associação de documentos e afirmações; âncora do Research Workspace por entidade. |
| `raw_records` | Proveniência de coleta para documentos/afirmações/evidências derivados de ingestão (referência por FK). |
| `sources` (ingestão) | Proveniência operacional opcional quando documento/afirmação/evidência se origina de coleta registrada; manter semântica de Source Registry intacta. |
| `audit_events`, `data_changes`, `processing_events` | Rastreabilidade de ações, mutações e etapas determinísticas de D2. |
| `entity_identifiers`, `entity_aliases`, `relationships` (D4), `agent_runs` | Sem alteração funcional em D2 (compatibilidade preservada). |

### 3.2 `documents` (existente) — extensão aditiva proposta

**Objetivo:** tornar `documents` adequado a cadastro manual e a metadados/proveniência/controle exigidos, sem quebrar registros futuros já compatíveis com o schema Foundation.

| Campo (proposto) | Tipo | Nulo | Notas |
|---|---|---|---|
| `source_id` (existente) | FK `sources.id` | **tornar anulável** (migração aditiva) | Permitir documentos registrados manualmente sem fonte de ingestão; quando presente, mantém proveniência de coleta. |
| `document_type` | String(100) | sim, index | Tipo/classificação do documento (ex.: contrato, notícia, relatório, registro público, nota interna, comunicação, outro). Vocabulário controlado na aplicação (extensível). |
| `description` | Text | sim | Descrição/resumo curto fornecido pelo usuário. |
| `origin_type` | String(50) | sim | `manual`, `ingestion`, `external_reference`, `derived` (controlado). |
| `source_locator` | Text | sim | URL/referência/localizador de origem (externo ou canônico). |
| `occurred_at` | DateTime(tz) | sim | Data de ocorrência/fato descrito, quando distinta de publicação/captura. |
| `captured_at` | DateTime(tz) | sim | Data de captura/consulta/obtenção. |
| `content_hash` | String(128) | sim, index | Hash do conteúdo (ex.: SHA-256) para integridade/deduplicação; distinto/compatível com `checksum` existente. |
| `verification_status` | String(50) | não, default `nao_verificado` | Estado de verificação do documento/artefato. |
| `access_level` | String(50) | sim | Classificação de acesso/visibilidade local (ex.: interno, restrito, confidencial), para controle mínimo. |
| `license_terms` | Text | sim | Notas de licença/termos/permissão de uso/armazenamento. |
| `is_reference_only` | Boolean | não, default false | Verdadeiro quando não há cópia local (apenas referência/metadados). |
| `research_source_id` | FK `research_sources.id` (nova) | sim, index | Vínculo à fonte de pesquisa D2 (ver 3.3). |
| `created_at`, `updated_at` | DateTime(tz) | não | Padronização com `TimestampMixin` (aditivo; backfill com `collected_at`/now quando necessário). |

**Índices adicionais sugeridos:** (`research_source_id`), (`document_type`), (`content_hash`), (`verification_status`), (`published_at`), (`captured_at`).

**Restrições/invariantes de aplicação (planejadas):** ao menos uma âncora de proveniência/contexto (`source_id` de ingestão ou `raw_record_id` ou `research_source_id` ou `source_locator`); se `storage_path` informado/arquivo armazenado então `content_hash/checksum` e metadados de integridade obrigatórios; `is_reference_only=true` incompatível com armazenamento de cópia local.

### 3.3 `research_sources` (nova) — fonte de pesquisa/referência do dossiê

**Objetivo:** atender integralmente o escopo A (“Sources — Fontes”) sem conflitar com `sources` de ingestão.

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | String(36) PK | não | UUID. |
| `name` | String(300) | não | Nome identificável da fonte. |
| `source_type` | String(100) | não, index | Tipo (site, publicação, documento oficial, base de dados, entrevista, comunicação, registro interno, etc.). |
| `domain` | String(255) | sim | Domínio/entidade provedora quando aplicável. |
| `url` | Text | sim | URL principal/referência. |
| `description` | Text | sim | Descrição/contexto. |
| `classification` | String(100) | sim, index | Classificação da fonte (ex.: pública, oficial, privada, especializada, primária/secundária — vocabulário controlado). |
| `consulted_at` | DateTime(tz) | sim | Data de consulta. |
| `last_verified_at` | DateTime(tz) | sim | Última verificação. |
| `reliability_status` | String(50) | não, default `nao_avaliada`, index | Estado de confiabilidade (ex.: `nao_avaliada`, `baixa`, `media`, `alta`, `contestada`). |
| `reliability_justification` | Text | sim | Justificativa da avaliação de confiabilidade. |
| `verification_status` | String(50) | não, default `nao_verificado` | Estado de verificação da fonte no contexto do dossiê. |
| `ingestion_source_id` | FK `sources.id` | sim, index, SET NULL | Vínculo opcional à fonte operacional de ingestão (proveniência técnica), quando aplicável. |
| `metadata_json` | JSON | sim | Metadados adicionais controlados. |
| `created_by` | String(100) | sim | Ator local. |
| `created_at`, `updated_at` | DateTime(tz) | não | Timestamps. |

**Índices:** (`source_type`, `reliability_status`), (`domain`), (`last_verified_at`).

### 3.4 `document_entity_links` (nova) — associação documento↔entidade (N:N)

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | String(36) PK | não | UUID. |
| `document_id` | FK `documents.id` CASCADE | não, index | Documento. |
| `entity_id` | FK `entities.id` CASCADE | não, index | Entidade do dossiê. |
| `role` | String(100) | sim | Papel/contexto da associação (ex.: mencionado, sujeito, parte, referência). |
| `notes` | Text | sim | Observação contextual. |
| `created_at` | DateTime(tz) | não | Timestamp. |

**Restrição:** unicidade lógica (`document_id`, `entity_id`, `role` normalizado) para evitar duplicatas triviais (índice único composto quando `role` aplicável, ou chave de deduplicação na aplicação).

### 3.5 `extracted_claims` (existente) — extensão aditiva proposta

**Objetivo:** suportar afirmações manuais/determinísticas vinculadas a entidades, com justificativa e tratamento de conflitos, preservando semântica atual.

| Campo (proposto) | Tipo | Nulo | Notas |
|---|---|---|---|
| `source_id` (existente) | FK `sources.id` | **tornar anulável** (migração aditiva) | Permitir claim manual sem fonte de ingestão; origem pode vir de `research_source_id`/`document_id`. |
| `entity_id` | FK `entities.id` | sim (fase 1) / alvo obrigatório por regra de aplicação | Entidade principal relacionada (consulta eficiente por dossiê). Ver 3.6 para casos multi-entidade. |
| `research_source_id` | FK `research_sources.id` | sim, index, SET NULL | Fonte de pesquisa associada. |
| `claim_origin` | String(50) | não, default `manual` | `manual`, `deterministic_import`, `assisted` (futuro, não ativo) — explicita procedência do registro. |
| `justification` | Text | sim | Justificativa de confiança/estado/interpretação (essencial para inferência/hipótese). |
| `registered_at` | DateTime(tz) | sim | Data de registro no sistema (além de `created_at`). |
| `conflict_status` | String(50) | não, default `none`, index | `none`, `contested`, `conflicting`, `under_review` (derivável/atualizável por regras determinísticas a partir de relações de conflito). |
| `metadata_json` | JSON | sim | Metadados adicionais controlados. |

**Índices adicionais:** (`entity_id`, `verification_status`), (`entity_id`, `claim_type`), (`research_source_id`), (`conflict_status`).

**Invariantes de aplicação:** `claim_text` obrigatório; `claim_type` em vocabulário conhecido; se `claim_type` em {`inferencia`,`hipotese`,`previsao`} exigir justificativa/registro explícito e nunca marcar como fato verificado automaticamente; toda claim exibida no Research Workspace deve ter ao menos uma entidade relacionada (via `entity_id` ou vínculo 3.6) e origem/proveniência identificável.

### 3.6 `claim_entity_links` (nova, recomendada) — associação claim↔entidade (N:N)

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | String(36) PK | não | UUID. |
| `claim_id` | FK `extracted_claims.id` CASCADE | não, index | Afirmação. |
| `entity_id` | FK `entities.id` CASCADE | não, index | Entidade. |
| `relevance` | String(100) | sim | Papel/relevância da entidade na afirmação. |
| `created_at` | DateTime(tz) | não | Timestamp. |

**Justificativa:** o escopo exige afirmações relacionadas a entidades; N:N evita limitação a uma única entidade e suporta evolução (ex.: afirmação envolvendo múltiplas partes) sem remodelar depois. `entity_id` em `extracted_claims` (3.5) pode ser mantido como “entidade principal” opcional para performance/compatibilidade, com consistência garantida pelo serviço.

### 3.7 `claim_conflicts` (nova) — identificação explícita de afirmações contraditórias

| Campo | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | String(36) PK | não | UUID. |
| `claim_id` | FK `extracted_claims.id` CASCADE | não, index | Afirmação A. |
| `conflicting_claim_id` | FK `extracted_claims.id` CASCADE | não, index | Afirmação B. |
| `conflict_type` | String(100) | não | Tipo (ex.: contradição direta, inconsistência temporal, divergência de valor, contestação). |
| `description` | Text | sim | Descrição/justificativa do conflito. |
| `status` | String(50) | não, default `open`, index | `open`, `under_review`, `resolved`, `dismissed` (resolução sempre manual/registrada). |
| `detected_by` | String(50) | não, default `user` | `user` (D2); valores futuros possíveis, sem automação ativa. |
| `created_by` | String(100) | sim | Ator local. |
| `created_at`, `updated_at` | DateTime(tz) | não | Timestamps. |

**Restrições:** proibir auto-conflito (`claim_id != conflicting_claim_id`); unicidade normalizada do par (A,B) independente de ordem (implementada por convenção de ordenação de IDs ou índice único calculado na aplicação + validação); atualização de `conflict_status` em claims afetadas de forma determinística e auditável.

### 3.8 `evidence` (existente) — extensão aditiva proposta

| Campo (proposto) | Tipo | Nulo | Notas |
|---|---|---|---|
| `source_id` (existente) | FK `sources.id` | **tornar anulável** | Permitir evidência ancorada em fonte de pesquisa/documento sem fonte de ingestão. |
| `document_id` | FK `documents.id` | sim, index, SET NULL | Documento que sustenta/contextualiza/contesta. |
| `research_source_id` | FK `research_sources.id` | sim, index, SET NULL | Fonte de pesquisa associada. |
| `evidence_type` | String(100) | sim, index | Tipo (trecho textual, metadado, registro, imagem/referência, documento integral, etc.). |
| `relation_type` | String(50) | não, default `supports`, index | `supports`, `contests`, `contextualizes` (conforme escopo D). |
| `location_json` | JSON | sim | Localização precisa estruturada (página, seção, offset, intervalo, seletor, coordenada, linha) quando aplicável. |
| `excerpt` | Text | sim | Trecho/referência textual (complementar a `snippet` existente para migração suave). |
| `updated_at` | DateTime(tz) | sim (ou não com backfill) | Padronização de atualização. |

**Invariantes de aplicação:** toda evidência deve referenciar ao menos uma âncora rastreável (`document_id` ou `research_source_id` ou `raw_record_id` ou `source_id` ou `locator`); `relation_type` restrito aos valores permitidos; vínculo consistente com a claim.

### 3.9 Diagrama lógico de relações (D2 — foco)

- `entities (1) —— (N) document_entity_links (N) —— (1) documents`
- `entities (1) —— (N) claim_entity_links (N) —— (1) extracted_claims` (+ `extracted_claims.entity_id` opcional como principal)
- `extracted_claims (1) —— (N) evidence`
- `extracted_claims (1) —— (N) claim_conflicts (N) —— (1) extracted_claims`
- `research_sources (1) —— (N) documents` (opcional)
- `research_sources (1) —— (N) extracted_claims` (opcional)
- `research_sources (1) —— (N) evidence` (opcional)
- `documents (1) —— (N) evidence` (opcional)
- `sources` de ingestão / `raw_records` permanecem como proveniência técnica opcional referenciável por `documents`, `extracted_claims`, `evidence` (reuso Foundation).

### 3.10 Considerações de integridade e compatibilidade
- Migrações **somente aditivas**: novas tabelas/colunas/índices/FKs; alterações de nulabilidade apenas quando seguras e necessárias (ex.: `documents.source_id`, `extracted_claims.source_id`, `evidence.source_id` para suportar entrada manual) com backfill/defaults adequados e preservação de dados existentes.
- Nenhuma remoção/renomeação destrutiva de colunas Foundation; manter `snippet`, `checksum`, campos temporais existentes e semântica de enums já em uso.
- `PRAGMA foreign_keys=ON` (já aplicado) deve ser considerado no desenho das migrações SQLite (tabelas novas e FKs). Operações que exigirem recriação de tabela (limitação SQLite para alterar nulabilidade/constraints em alguns casos) devem ser planejadas como migração segura com cópia de dados, preservando IDs e referências.
- **Não popular automaticamente** `documents`/`extracted_claims`/`evidence` a partir de `raw_records` nesta etapa.

## 4. Estruturas existentes e novas estruturas

### 4.1 Matriz de decisão (reuso x extensão x criação)

| Estrutura | Decisão | Justificativa | Impacto |
|---|---|---|---|
| `entities`, `entity_identifiers`, `entity_aliases` | **Reutilizar (sem alteração)** | Perfil canônico e auxiliares D1 estáveis. | Nenhum; consumo por FK/consultas. |
| `sources` (ingestão) | **Reutilizar por referência (sem alteração estrutural)** | Proveniência operacional válida quando aplicável; semântica distinta de fonte de pesquisa. | Nenhum no schema; possível link opcional via `research_sources.ingestion_source_id`. |
| `raw_records` | **Reutilizar por referência (sem alteração estrutural)** | Proveniência/deduplicação de coleta já implementada. | Nenhum. |
| `documents` | **Estender (aditivo)** | Base correta para artefatos, mas incompleta para D2 (entidades, metadados, manual, proveniência rica). Evita tabela paralela de “documentos de dossiê”. | Migração aditiva; ajuste de nulabilidade/colunas/índices; compatibilidade preservada. |
| `extracted_claims` | **Estender (aditivo)** | Já possui semântica central (tipo epistemológico, verificação, versionamento, datas). Faltam entidade, justificativa, origem e conflitos. | Migração aditiva; evolução de serviços/schemas. |
| `evidence` | **Estender (aditivo)** | Base de vínculo claim-evidência existe; faltam papel/tipo/localização precisa e vínculos a documento/fonte de pesquisa. | Migração aditiva. |
| `data_changes`, `audit_events`, `processing_events` | **Reutilizar (sem alteração)** | Rastreabilidade transversal suficiente. | Uso ampliado por D2. |
| `relationships` | **Não alterar / não usar para D2** | Domínio de conexões entre entidades (D4). Conflitos D2 são entre afirmações. | Nenhum. |
| `agent_runs` | **Não alterar** | Fora de escopo D2 (IA assistida futura opcional). | Nenhum. |
| **`research_sources`** | **Criar (nova)** | Necessária para cumprir escopo A com semântica própria sem poluir `sources` de ingestão. | Nova tabela, FKs, índices. |
| **`document_entity_links`** | **Criar (nova)** | Associação N:N documento↔entidade exigida; não suportada pelo schema atual. | Nova tabela, FKs, unicidade lógica. |
| **`claim_entity_links`** | **Criar (nova, recomendada)** | Afirmações relacionadas a uma ou mais entidades com consulta eficiente e evolução segura. | Nova tabela, FKs, índices. |
| **`claim_conflicts`** | **Criar (nova)** | Identificação explícita e rastreável de contradições entre afirmações. | Nova tabela, FKs, restrições de unicidade/consistência. |

### 4.2 Estruturas avaliadas e descartadas (evitar redundância)
- **Duplicar `sources` para pesquisa copiando campos operacionais:** descartado; cria redundância e ambiguidade. Preferir `research_sources` com vínculo opcional `ingestion_source_id`.
- **Criar tabela paralela `dossier_documents` ignorando `documents`:** descartado; `documents` já existe e é a âncora natural (com extensão).
- **Modelar conflito apenas em JSON livre dentro de `extracted_claims`:** descartado; dificulta consulta, integridade e rastreabilidade. Preferir `claim_conflicts` + status derivado.
- **Usar `relationships` (entidade↔entidade) para conflito entre claims:** descartado por incompatibilidade semântica e acoplamento indevido com D4.

## 5. Migrações necessárias

> Todas aditivas e versionadas em Alembic, encadeadas após `b7d1e2f3a4c5` (head atual de D1). **Não executar nesta etapa de planejamento.**

### 5.1 Estratégia e ordem das migrações (proposta)

| Ordem | Revisão (nome proposto) | Conteúdo | Risco/nota |
|---|---|---|---|
| M1 | `d2_research_sources` | Criar `research_sources` (campos, FKs opcionais para `sources`, índices). | Baixo; tabela nova independente. |
| M2 | `d2_documents_extend_and_links` | Estender `documents` (novas colunas, `created_at/updated_at`, `research_source_id` FK, índices); criar `document_entity_links`; ajustar nulabilidade de `documents.source_id` conforme capacidade SQLite (possível recriação controlada da tabela com preservação de dados/IDs/FKs/índices). | **Médio (SQLite):** alteração de nulabilidade pode exigir `batch_alter_table`/recriação; plano de migração deve copiar dados e validar contagens. |
| M3 | `d2_claims_extend_and_links` | Estender `extracted_claims` (novas colunas/FKs, índices); criar `claim_entity_links`; ajustar nulabilidade de `extracted_claims.source_id` se necessário. | **Médio (SQLite):** mesma cautela de M2. |
| M4 | `d2_claim_conflicts` | Criar `claim_conflicts` (FKs para `extracted_claims`, índices, unicidade lógica/checagens aplicáveis). | Baixo/médio; garantir integridade de pares e ausência de auto-referência. |
| M5 | `d2_evidence_extend` | Estender `evidence` (novas colunas/FKs para `documents` e `research_sources`, `updated_at`, índices); ajustar nulabilidade de `evidence.source_id` se necessário. | **Médio (SQLite)**. |

> Alternativa aceitável: consolidar em menos revisões desde que cada passo permaneça atômico, testável e reversível (downgrade aditivo seguro). A decisão final de granularidade deve priorizar clareza e segurança no SQLite.

### 5.2 Regras de migração e segurança de dados
- **Backfill determinístico:** novos campos NOT NULL com defaults seguros (`verification_status='nao_verificado'`, `claim_origin='manual'` para registros futuros, `conflict_status='none'`, `relation_type='supports'`, `is_reference_only=false`, `reliability_status='nao_avaliada'`), timestamps preenchidos quando aplicável.
- **Preservação de integridade:** manter PKs/FKs existentes e dados de D1/Foundation intactos; validar contagens antes/depois em testes de migração.
- **Downgrade:** definido para remover apenas artefatos introduzidos por D2 e reverter extensões quando viável, com consciência das limitações SQLite (documentar passos de recriação inversa no script de migração).
- **Ambiente:** migrações testadas exclusivamente em bancos temporários nos testes automatizados; aplicação em `backend/data/scout.db` somente após autorização explícita de execução (fora deste planejamento).

### 5.3 Impactos esperados
- Aumento do número de tabelas de domínio (17 → 21, se adotadas todas as novas) e de índices; volume compatível com uso local/SQLite.
- Necessidade de atualização de modelos ORM, exportações (`knowledge/models/__init__.py`) e consultas de serviço/API/UI.
- Nenhuma alteração no pipeline de ingestão Foundation (F) obrigatória em D2; `documents` derivados de coleta permanecem fora de escopo, mas o schema passa a suportá-los no futuro.

## 6. Endpoints e contratos

> Prefixo base: `/api/v1/dossiers`. Convenções D1: JSON, validação Pydantic, erros 404/422/409 conforme caso, paginação `limit/offset` + `total`, timestamps ISO-8601, sem exposição remota. Todas as mutações devem registrar `audit_events` e `data_changes`; operações determinísticas relevantes podem registrar `processing_events`.

### 6.1 Research Sources (Fontes de pesquisa)

| Método | Rota | Descrição | Contrato (proposta) |
|---|---|---|---|
| POST | `/research-sources` | Criar fonte de pesquisa | Body: `ResearchSourceCreate` (nome, tipo, domínio, url, descrição, classificação, datas consulta/verificação, confiabilidade/justificativa, verificação, `ingestion_source_id?`, metadados). Resp 201: `ResearchSourceDetail`. |
| GET | `/research-sources` | Listar/pesquisar fontes | Query: `q`, `source_type`, `classification`, `reliability_status`, `verification_status`, `consulted_from/to`, `verified_from/to`, `sort`, `limit/offset`. Resp 200: `ResearchSourceListResponse`. |
| GET | `/research-sources/{source_id}` | Detalhar fonte | Resp 200: `ResearchSourceDetail` (inclui contagens/refs resumidas a documentos/claims/evidências quando útil). |
| PATCH | `/research-sources/{source_id}` | Atualizar fonte (avaliação, verificação, metadados) | Body: `ResearchSourceUpdate` parcial. Resp 200: detalhe atualizado. |

### 6.2 Documents (Documentos)

| Método | Rota | Descrição | Contrato (proposta) |
|---|---|---|---|
| POST | `/entities/{entity_id}/documents` | Registrar documento e associar à entidade (cadastro manual/contextual) | Body: `DocumentCreate` (título, descrição, tipo, origem, locators, datas, idioma, metadados, hash/checksum/size/mime quando informado, `research_source_id?`, referências a `raw_record_id`/`ingestion_source_id` quando aplicável, `storage_path`/upload ref, flags de permissão/licença/referência-only, `entity_role?`, entidades adicionais?). Resp 201: `DocumentDetail`. |
| GET | `/entities/{entity_id}/documents` | Listar documentos da entidade (Research Workspace) | Query: `q`, `document_type`, `verification_status`, `origin_type`, `research_source_id`, `has_file`, `date_from/to`, `sort`, `limit/offset`. Resp 200: `DocumentListResponse`. |
| GET | `/documents/{document_id}` | Detalhar documento | Resp 200: `DocumentDetail` (metadados, proveniências, entidades vinculadas, integridade, evidências/claims relacionadas resumidas). |
| PATCH | `/documents/{document_id}` | Atualizar metadados/estado/classificação | Body: `DocumentUpdate`. Resp 200: detalhe. |
| POST | `/documents/{document_id}/entities` | Associar entidade(s) adicional(is) | Body: `DocumentEntityLinkCreate` (entity_id(s), role/notes). Resp 201/200. |
| DELETE | `/documents/{document_id}/entities/{entity_id}` | Remover associação (com regra/registro) | Resp 204/200 com rastreabilidade. |

**Nota de armazenamento/arquivo:** upload/registro de arquivo local deve ser tratado por endpoint dedicado e determinístico (ex.: `POST /documents/upload` ou multipart em criação) que grava em `settings.documents_dir` apenas sob validação explícita (tamanho/mime/configuração), calcula hash SHA-256, registra caminho e nunca expõe fora do loopback. Alternativa mínima: registro de `storage_path` já existente/local previamente controlado. O plano recomenda definir contrato explícito na implementação, mantendo escopo conservador.

### 6.3 Claims (Afirmações)

| Método | Rota | Descrição | Contrato (proposta) |
|---|---|---|---|
| POST | `/entities/{entity_id}/claims` | Criar afirmação (manual prioritário) | Body: `ClaimCreate` (texto, `claim_type`, datas ocorrência/publicação/registro, `verification_status`, confiança, justificativa, `document_id?`, `research_source_id?`, `raw_record_id?`, entidades adicionais/roles?). Resp 201: `ClaimDetail`. |
| GET | `/entities/{entity_id}/claims` | Listar afirmações da entidade | Query: `q`, `claim_type`, `verification_status`, `conflict_status`, `has_evidence`, `research_source_id`, `document_id`, `date_from/to`, `sort`, `limit/offset`. Resp 200: `ClaimListResponse`. |
| GET | `/claims/{claim_id}` | Detalhar afirmação | Resp 200: `ClaimDetail` (proveniência, entidades, evidências, conflitos, histórico de versão/supersessão quando aplicável). |
| PATCH | `/claims/{claim_id}` | Atualizar estado/classificação/justificativa (explícito) | Body: `ClaimUpdate`. Resp 200. |
| POST | `/claims/{claim_id}/conflicts` | Registrar contradição/conflito com outra afirmação | Body: `ClaimConflictCreate` (`conflicting_claim_id`, tipo, descrição, status inicial). Resp 201: `ClaimConflictDetail`. |
| PATCH | `/claims/{claim_id}/conflicts/{conflict_id}` | Atualizar status/descrição do conflito | Body: `ClaimConflictUpdate`. Resp 200. |
| GET | `/entities/{entity_id}/conflicts` | Listar conflitos relevantes ao dossiê | Query: filtros por status/tipo. Resp 200: `ClaimConflictListResponse`. |

### 6.4 Evidence (Evidências)

| Método | Rota | Descrição | Contrato (proposta) |
|---|---|---|---|
| POST | `/claims/{claim_id}/evidence` | Associar evidência à afirmação | Body: `EvidenceCreate` (tipo, `relation_type`, `document_id?`, `research_source_id?`, `raw_record_id?`, `locator`, `location_json`, trecho/excerpt/snippet, nota, datas, confiança/verificação). Resp 201: `EvidenceDetail`. |
| GET | `/claims/{claim_id}/evidence` | Listar evidências da afirmação | Resp 200: `EvidenceListResponse`. |
| GET | `/evidence/{evidence_id}` | Detalhar evidência | Resp 200: `EvidenceDetail`. |
| PATCH | `/evidence/{evidence_id}` | Atualizar evidência/localização/estado | Body: `EvidenceUpdate`. Resp 200. |

### 6.5 Research Workspace (visão agregada, leitura)

| Método | Rota | Descrição | Contrato (proposta) |
|---|---|---|---|
| GET | `/entities/{entity_id}/research/summary` | Resumo determinístico do workspace | Resp 200: contagens e indicadores persistidos/derivados de forma determinística (documentos, fontes consultadas, afirmações por tipo/verificação, evidências, pendentes de verificação, conflitos abertos), sem inferência. |
| GET | `/entities/{entity_id}/research/timeline` (opcional, se estritamente documental/epistêmico) | Linha temporal de registros de pesquisa | **Cautela:** não conflitar com D3 (Relationship History/interações). Se incluído, limitar a eventos de registro/publicação/ocorrência de documentos e afirmações com rótulo claro “Histórico de pesquisa e evidências (D2)”. |

### 6.6 Schemas, validações e permissões (planejados)
- **Schemas Pydantic:** `ResearchSource(Create/Update/Detail/Summary/List)`, `Document(Create/Update/Detail/Summary/List)`, `Claim(Create/Update/Detail/Summary/List)`, `Evidence(Create/Update/Detail/Summary/List)`, `ClaimConflict(...)`, respostas de workspace e modelos de vínculo; reutilizar padrões de `ConfigDict(from_attributes=True)` e tipagem estrita.
- **Validações:** campos obrigatórios por caso (nome/título/texto), normalização de URLs/domínios quando informado, vocabulários controlados (`claim_type`, `verification_status`, `relation_type`, `origin_type`, confiabilidade), coerência temporal básica (não bloquear excessivamente, mas sinalizar/validar formatos), exigência de âncora de proveniência, prevenção de auto-conflito e duplicatas lógicas (hash de documento, par de conflito).
- **Permissões/controle:** execução local (loopback) no contexto atual sem autenticação multiusuário complexa; ainda assim, registrar `actor` local em auditoria/alterações, respeitar `access_level`/`is_reference_only`/licença e impedir armazenamento quando não permitido. Evolução para perfis/permissões finas permanece futura.
- **Erros:** 404 (entidade/recurso inexistente), 422 (validação/regra), 409 (duplicidade/conflito de unicidade), 400 apenas quando estritamente necessário; mensagens objetivas e seguras.

## 7. Componentes e fluxos de interface

> Preservar App Shell, rotas, Design System (Tailwind/shadcn/ui), padrões de estados (`PageState`/loading/erro/vazio/sucesso) e navegação por seções da página da entidade. Conteúdo em português, linguagem objetiva e adequada a contexto empresarial/patrimonial.

### 7.1 Research Workspace (dentro de `/dossiers/:entityId`)
Substituir o placeholder atual da seção **“Evidências e documentos” (D2)** por um workspace estruturado em abas/subseções (sem perder contexto da entidade):

1. **Resumo do workspace**
   - Contadores/indicadores determinísticos: documentos associados, fontes consultadas, afirmações registradas, evidências, itens pendentes de verificação, conflitos abertos.
   - Sinais visuais discretos (badges) para pendências/conflitos; sem gráficos pesados.

2. **Documentos**
   - Lista/tabela com busca e filtros (tipo, verificação, origem, presença de arquivo, fonte, período).
   - Ações: “Registrar documento” (formulário), abrir detalhe (painel lateral ou subpágina/modal acessível), editar metadados, associar entidades/fonte.
   - Detalhe: metadados, datas (publicação/ocorrência/captura/coleta), integridade (hash/checksum/tamanho/mime), proveniência (fonte de pesquisa, fonte de ingestão/raw_record, localizador), status/licença/acesso, entidades vinculadas, afirmações/evidências relacionadas.

3. **Fontes consultadas**
   - Lista e cadastro de fontes de pesquisa (nome, tipo, domínio/URL, classificação, confiabilidade + justificativa, consulta/última verificação).
   - Associação visível com documentos/afirmações que as referenciam.

4. **Afirmações**
   - Lista filtrável por tipo epistemológico, verificação, conflito, existência de evidência, origem/documento/fonte.
   - Exibição clara de rótulos: tipo (declaração, inferência, hipótese, etc.), verificação, confiança e justificativa, datas e proveniência.
   - Ações: “Registrar afirmação” (manual), editar estado/justificativa, registrar conflito com outra afirmação, visualizar evidências.

5. **Evidências**
   - Visualização por afirmação (e visão consolidada filtrável): trecho/localizador, tipo, relação (suporta/contesta/contextualiza), documento/fonte/raw_record, localização precisa.
   - Ação: “Adicionar evidência” vinculada à afirmação.

6. **Pendências e conflitos**
   - Visões focadas: itens `nao_verificado/em_verificacao` e conflitos `open/under_review` com acesso direto aos registros relacionados.
   - Nenhuma resolução automática; ações apenas de registro/atualização explícita.

### 7.2 Fluxos principais (UI)
- **Cadastro manual guiado:** formulários com campos obrigatórios mínimos, validação imediata, seleção/associação a entidade atual por padrão, escolha de fonte/documento existente ou criação encadeada quando fizer sentido (sem fluxos complexos).
- **Associação explícita:** controles claros para vincular documento↔entidades, claim↔entidade/documento/fonte, evidência↔claim/documento/fonte com indicação do papel/relação.
- **Rastreabilidade visível:** cada item exibe origem, datas relevantes, estado e (quando disponível) links/referências internas; metadados técnicos (hash, IDs) em área de detalhes.
- **Estados de interface:** carregamento, vazio (“nenhum documento/fonte/afirmação/evidência registrado”), erro recuperável (mensagem + retry) e sucesso; impedir apresentação de dados simulados.

### 7.3 Componentes frontend (planejados)
- Extensão de `frontend/src/lib/api/types.ts` e `client.ts` com recursos D2.
- Componentes em `frontend/src/components/dossiers/` (ex.: `ResearchWorkspace.tsx`, `ResearchSummary.tsx`, `DocumentsPanel.tsx`, `ResearchSourcesPanel.tsx`, `ClaimsPanel.tsx`, `EvidencePanel.tsx`, `ConflictsPanel.tsx`, formulários/dialogs reutilizáveis) seguindo padrões existentes (cards, badges, tabelas/listas, inputs, estados).
- Ajuste mínimo em `DossierEntityPage.tsx` para renderizar o workspace na seção `evidence` e manter placeholders de D3/D4/D5 inalterados.

### 7.4 UX, acessibilidade e performance
- Layout objetivo, hierarquia tipográfica clara, rótulos textuais (não depender só de cor) para estados epistemológicos/conflitos.
- Paginação e filtros no backend para listas; evitar carregamentos pesados; nenhuma atualização em tempo real complexa.
- Não introduzir dependências de UI novas; reutilizar componentes/padrões já disponíveis.

## 8. Plano de testes

> Objetivo: cobertura determinística e, preferencialmente, **offline** para a suíte padrão de D2, preservando compatibilidade com D1/Foundation.

### 8.1 Backend — migrações e modelo (pytest, DB temporário via Alembic)
- Aplicação da(s) migração(ões) D2 sobre head com D1 (`b7d1e2f3a4c5`): criação de tabelas novas, colunas/índices/FKs e ajustes de nulabilidade sem perda de dados existentes.
- Integridade referencial: FKs, cascades (ex.: remoção de entidade/documento/claim conforme regra definida), unicidades lógicas (vínculos, pares de conflito).
- Defaults e backfills: `verification_status`, `claim_origin`, `conflict_status`, `relation_type`, `reliability_status`, timestamps/flags.
- Compatibilidade: criação/leitura/atualização de entidades D1 continuam válidas após D2.

### 8.2 Backend — serviços e API (pytest, DB temporário, sem rede)
- **Fontes de pesquisa:** criar, listar/pesquisar/filtrar, detalhar, atualizar; validações e rastreabilidade (`audit_events`, `data_changes`).
- **Documentos:** cadastro e consulta, associação a uma/múltiplas entidades, metadados e datas, hash/checksum e detecção de duplicidade, integridade (campos obrigatórios quando há arquivo), respeito a `is_reference_only`/licença/permissão de armazenamento, vínculo opcional a `research_source`/`raw_record`/`source` de ingestão.
- **Afirmações:** criação manual vinculada à entidade, classificação epistemológica, verificação/confiança/justificativa, datas, proveniência, atualização explícita (sem promoção automática), versionamento/supersessão quando aplicável.
- **Evidências:** associação a claim com tipo e relação (`supports/contests/contextualizes`), vínculo a documento/fonte/localização precisa, rastreabilidade.
- **Conflitos:** registro entre afirmações, prevenção de auto-conflito/duplicidade, estados, impacto determinístico em indicadores de conflito, listagem por entidade.
- **Research workspace/consultas:** agregações determinísticas (pendentes, conflitos, contagens) coerentes com dados persistidos.
- **Erros e estados:** 404, 422, 409, respostas vazias, paginação/ordenação.
- **Regressão:** suíte Foundation + D1 integralmente verde.

### 8.3 Armazenamento e integridade de arquivos (determinístico, local temporário)
- Escrita em diretório temporário configurado para testes: criação de arquivo, cálculo de hash, registro de metadados e bloqueio quando armazenamento não permitido/referência-only.
- Sem dependências externas; sem operações fora dos diretórios controlados.

### 8.4 Frontend
- `npm run typecheck`, `npm run lint`, `npm run build` sem erros.
- Verificações de componentes/estados (quando houver infraestrutura de teste; caso contrário, validação estática e revisão de fluxos): renderização de listas vazias, erros, carregamento, rótulos epistemológicos, indicadores de conflito/pendência e ausência de simulação.
- Contratos de tipos cliente/API alinhados às respostas reais.

### 8.5 Estratégia offline e determinística (recomendação explícita)
- Novos testes D2 **não devem** depender de rede/recursos externos.
- Recomenda-se, como ajuste técnico associado à qualidade da suíte (a ser autorizado se implicar alteração fora do estrito escopo funcional), tornar opt-in/marcados os testes que realizam acesso HTTP real ao feed W3C, mantendo a suíte padrão offline e determinística. *Observação:* qualquer alteração de testes existentes requer autorização de implementação; este plano apenas registra a necessidade.

### 8.6 Critérios mínimos de execução para aceite de implementação
- Backend: ruff, mypy e pytest (incluindo D2 e regressão) aprovados.
- Frontend: typecheck, lint e build aprovados.
- Migração D2 validada em DB temporário; aplicação em DB local somente quando explicitamente autorizada.

## 9. Ordem incremental de implementação

> Execução recomendada em passos pequenos, cada um com validação antes do próximo. **Nenhum passo deve iniciar D3/D4/D5.**

1. **Preparação de contratos internos e modelos (base aditiva)**
   - Definir enums/vocabulários de aplicação para novos campos (tipos, origem, confiabilidade, relação de evidência, status de conflito) alinhados aos existentes.
   - Implementar migração M1 (`research_sources`) + modelo ORM + exportações.
2. **Research Sources — backend ponta a ponta**
   - Schemas, serviço (CRUD, normalização, validação, auditoria/alterações), endpoints e testes (migração/modelo/API).
3. **Documents — modelo e vínculos**
   - Migração M2 (extensão `documents` + `document_entity_links`, ajustes SQLite seguros) + modelos; atualizar mapeamentos.
4. **Documents — serviço, armazenamento controlado e API**
   - Lógica de registro manual, hash/deduplicação, integridade, associação a entidades/fonte de pesquisa, respeito a licença/permissão/referência-only; endpoints e testes (incluindo armazenamento em diretório temporário).
5. **Claims — modelo e vínculos**
   - Migração M3 (extensão `extracted_claims` + `claim_entity_links`) + modelos; regras de entidade principal/consistência.
6. **Claims e conflitos — backend**
   - Migração M4 (`claim_conflicts`), serviço de claims (manual, epistemologia/verificação/justificativa, proveniência), serviço de conflitos (registro/atualização determinística), endpoints e testes.
7. **Evidence — backend**
   - Migração M5 (extensão `evidence`), serviço e endpoints (tipo, relação suporta/contesta/contextualiza, localização precisa, vínculos), testes.
8. **Research Workspace — agregações e API de leitura**
   - Endpoint(s) de resumo/consultas consolidadas por entidade, filtros e indicadores de pendências/conflitos; testes de consistência determinística.
9. **Frontend — tipos/cliente e UI do workspace**
   - Extensão de `types.ts`/`client.ts`; implementação da seção D2 (resumo, documentos, fontes, afirmações, evidências, pendências/conflitos) com formulários manuais, estados e navegação; manutenção de placeholders D3/D4/D5.
10. **Integração, regressão e documentação**
    - Execução completa de validações (backend/frontend), ajustes finais de compatibilidade, atualização de `docs/modules/dossiers/{DOSSIERS_DATA_MODEL,API,UI,TEST_PLAN,CHANGELOG}.md` e status do projeto/roadmap conforme escopo efetivamente entregue.

> Cada passo deve ser concluído com testes relevantes verdes antes de avançar; qualquer ampliação de escopo requer autorização explícita.

## 10. Critérios de conclusão

D2 será considerada concluída quando, de forma validada e rastreável:

1. **Fontes de pesquisa:** cadastro, consulta, atualização, classificação/confiabilidade (com justificativa) e datas de consulta/verificação funcionam via API e UI, com proveniência preservada.
2. **Documentos:** cadastro e consulta com metadados completos, tipagem, origem/localização, datas (publicação/ocorrência/captura quando disponíveis), hash/integridade, controle de acesso/licença e associação a uma ou mais entidades; referência a conteúdo original respeitando permissões/licenças (armazenamento local apenas quando permitido).
3. **Afirmações:** registro manual com texto, entidade(s) relacionada(s), fonte/documento de origem quando aplicável, datas, classificação epistemológica, verificação, confiança e justificativa; sem promoção automática de inferência a fato.
4. **Evidências:** associação a afirmações com tipo, relação (suporta/contesta/contextualiza), trecho/localização precisa quando possível e vínculos rastreáveis a documentos/fontes/raw_records.
5. **Research Workspace:** seção D2 da página da entidade exibe documentos, fontes, afirmações, evidências, pendências de verificação e conflitos com estados claros, sem dados simulados.
6. **Conflitos:** afirmações contraditórias podem ser identificadas, registradas, consultadas e atualizadas explicitamente.
7. **Rastreabilidade e integridade:** mutações relevantes geram `audit_events`/`data_changes` (e `processing_events` quando aplicável); integridade referencial e regras de consistência asseguradas.
8. **Migrações e compatibilidade:** migrações aditivas aplicáveis com sucesso em banco limpo e sobre estado D1; dados e fluxos D1/Foundation preservados.
9. **Qualidade:** testes automatizados previstos para D2 e regressões Foundation/D1 aprovados; frontend (typecheck/lint/build) aprovado; comportamento determinístico e local-first mantido.
10. **Documentação:** artefatos do módulo e status do projeto atualizados para refletir o escopo efetivamente entregue e limitações remanescentes.

## 11. Riscos técnicos e operacionais

| Risco | Impacto | Mitigação planejada |
|---|---|---|
| **Alteração de nulabilidade em SQLite** (`source_id` em `documents`/`extracted_claims`/`evidence`) pode exigir recriação de tabelas | Migração complexa; risco a FKs/índices/dados se mal executada | Usar `batch_alter_table`/recriação controlada com cópia explícita, preservação de IDs, recriação de índices/FKs e testes de migração com contagens/consultas de verificação em DB temporário. |
| **Sobrecarga semântica entre `sources` (ingestão) e fontes de pesquisa** | Confusão de domínio, contratos ambíguos, regressões em ingestão | Manter `sources` intacto; introduzir `research_sources` com vínculo opcional `ingestion_source_id`; documentar claramente a distinção em modelo, API e UI. |
| **Armazenamento de arquivos e controle de acesso/licença** | Retenção indevida, inconsistência de integridade, exposição acidental | Escrita apenas em `documents_dir` sob regras explícitas; hash obrigatório para cópias locais; `is_reference_only` e `license_terms/access_level`; nunca expor fora do loopback; sem upload remoto. |
| **Crescimento de complexidade de consultas (N:N, filtros, agregações)** | Lentidão em listas/workspace, consultas N+1 | Índices planejados, paginação obrigatória, consultas agregadas dedicadas e carregamento seletivo (resumos vs detalhes). |
| **Consistência de conflitos e estados derivados** | Indicadores divergentes do estado real | Regras determinísticas centralizadas no serviço, atualizações transacionais, testes de invariantes (ex.: conflito aberto ⇒ claims marcadas coerentemente). |
| **Promoção indevida de inferência/hipótese a fato** | Violação do princípio epistemológico do produto | Vocabulário controlado, validações de fluxo, UI com rótulos explícitos, exigência de justificativa/ação explícita para estados de verificação fortes. |
| **Dependência de rede em testes existentes** | Suíte padrão não determinística/offline | Planejar novos testes D2 sem rede; recomendar (mediante autorização) tornar opt-in os testes de rede legados. |
| **Expansão de escopo para D3/D4/D5 ou automação/IA** | Atraso, acoplamento prematuro, violações de restrição | Adesão estrita ao escopo D2, placeholders preservados, interfaces futuras apenas documentadas. |
| **Compatibilidade com D1/Foundation** | Regressões em CRUD de entidades, navegação e contratos existentes | Bateria de regressão, migrações aditivas, versionamento de contratos e evolução compatível de endpoints/schemas. |

## 12. Estimativa de complexidade por subetapa

> Escala relativa: **Baixa** (mudança localizada), **Média** (múltiplas camadas com risco moderado), **Alta** (modelagem/migração/integração sensíveis). Estimativas são técnicas (esforço relativo), não compromisso temporal.

| Subetapa (ordem de implementação) | Complexidade | Justificativa |
|---|---|---|
| 1. Preparação de contratos internos e M1 (`research_sources`) | Média | Nova entidade de domínio, migração e alinhamento de vocabulários, porém isolada e aditiva. |
| 2. Research Sources — backend ponta a ponta | Média | CRUD completo, validações, filtros/paginação e rastreabilidade no padrão D1. |
| 3. Documents — modelo e vínculos (M2) | **Alta** | Extensão de tabela existente com possível recriação SQLite para nulabilidade, N:N entidade-documento e preservação de integridade. |
| 4. Documents — serviço, armazenamento controlado e API | **Alta** | Regras de integridade/hash/deduplicação, permissões/licença, armazenamento local controlado e múltiplas associações/proveniências. |
| 5. Claims — modelo e vínculos (M3) | **Alta** | Extensão de estrutura central, vínculo a entidades (N:N + principal), compatibilidade de dados/consultas e ajustes SQLite. |
| 6. Claims e conflitos — backend (M4 + lógica) | **Alta** | Semântica epistemológica rigorosa, conflitos rastreáveis com invariantes e impactos em indicadores/consultas. |
| 7. Evidence — backend (M5 + API) | Média-Alta | Extensões de vínculos/proveniência e localização estruturada; integração consistente com claims/documentos/fontes. |
| 8. Research Workspace — agregações e API de leitura | Média | Consultas consolidadas determinísticas e paginação/filtros; depende da qualidade do modelo anterior. |
| 9. Frontend — tipos/cliente e UI do workspace | **Alta** | Superfície ampla (múltiplos painéis, formulários, estados, rótulos epistemológicos/conflitos) mantendo Design System e sem simulação. |
| 10. Integração, regressão e documentação | Média | Validação cruzada, ajustes de compatibilidade e atualização documental consistente com entrega real. |

**Complexidade global D2:** **Alta** (predominância de mudanças estruturais sensíveis em SQLite, modelagem de proveniência/epistemologia/conflitos e UI de workspace), viável de forma incremental desde que executada em passos pequenos com validação contínua.

---

## Resumo executivo do planejamento
- **Diagnóstico:** D1 e Foundation fornecem base sólida (entidades, proveniência, rastreabilidade, ingestão de `raw_records`), mas as tabelas `documents`/`extracted_claims`/`evidence` são mínimas e não cobrem associação a entidades, cadastro manual completo, fonte de pesquisa de dossiê, justificativas, conflitos e localização precisa.
- **Arquitetura:** extensão aditiva e determinística do módulo Dossiers, com `research_sources` como nova estrutura de fonte de pesquisa (vínculo opcional à ingestão), extensão de `documents`/`extracted_claims`/`evidence`, e vínculos N:N/conflicts explícitos; armazenamento local controlado em `backend/data/documents/`.
- **Dados:** 4 novas tabelas propostas (`research_sources`, `document_entity_links`, `claim_entity_links`, `claim_conflicts`) + extensões aditivas nas 3 tabelas existentes de conteúdo/prova; migrações Alembic em cadeia pós-`b7d1e2f3a4c5` com cuidado especial a limitações SQLite.
- **API/UI:** endpoints e contratos para fontes, documentos, afirmações, evidências, conflitos e resumo de workspace; Research Workspace integrado à página da entidade substituindo o placeholder D2, sem simulação e com rotulagem epistemológica clara.
- **Testes:** cobertura determinística em DB temporário (migração, integridade, CRUD/associações/conflitos, agregações) e validações frontend; recomendação de manter suíte padrão offline.
- **Implementação:** 10 passos incrementais, priorizando modelo/migrações seguras e backend determinístico antes da UI e consolidação documental.
- **Conformidade:** sem IA obrigatória, sem coleta indiscriminada, sem promoção automática a fato, sem D3/D4/D5 e sem alterações fora de escopo autorizado.

**Próxima ação aguardada:** aprovação explícita deste plano para autorizar (em etapa separada) a implementação incremental de D2 conforme a ordem proposta.
