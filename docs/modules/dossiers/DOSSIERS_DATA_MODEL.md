# DOSSIERS — Modelo de Dados (D1: Entity Profiles, D2: Research & Evidence, D3: Relationship History)

> **D1:** migração `b7d1e2f3a4c5` (`dossiers_d1_entity_profiles`, filha de `426757a848bb`).  
> **D2:** migrações aditivas `c1d2e3f4a5b6` → `d2e3f4a5b6c7` → `e3f4a5b6c7d8` → `f4a5b6c7d8e9` → `a5b6c7d8e9f0` (após `b7d1e2f3a4c5`).  
> **D3:** migração aditiva `b6c7d8e9f0a1` (`d3_relationship_history`, filha de `a5b6c7d8e9f0`), **implementada, validada e publicada**, aplicada ao DB local.  
> **Banco:** SQLite/Alembic (local-first). Cadeia validada em banco temporário (`alembic upgrade head`).

## 1. Princípios de reuso
- **`entities`** permanece a entidade canônica do dossiê (não duplicada). D1 estende `entities` e adiciona identificadores/aliases; D2 associa documentos/afirmações; D3 associa interações (histórico) à entidade âncora.
- Reuso de proveniência/rastreabilidade transversais: `audit_events`, `data_changes`, `processing_events` (quando aplicável) e referências opcionais a estruturas de ingestão/Foundation (`sources` operacionais, `raw_records`).
- **Separações semânticas:** `sources` (ingestão operacional) ≠ `research_sources` (fontes de pesquisa do dossiê). D3 (interações/timeline) ≠ D2 (pesquisa/evidências/afirmações). `relationships` permanece **reservado a D4** (conexões entre entidades) e não é utilizado em D3.

## 2. D1 — Entity Profiles

### 2.1 Alterações em `entities` (aditivas)
| Coluna | Tipo | Notas |
|---|---|---|
| `description` | Text, nullable | Descrição curta para cabeçalho do dossiê. |
| `profile_status` | String(50), not null, default `active`, index | Estado cadastral do perfil. |
| `primary_location` | String(300), nullable | Localização em nível apropriado. |
| `profile_data` | JSON, nullable | Atributos por tipo de entidade e metadados. |

Campos existentes preservados. Tipos suportados `person|company|economic_group|institution|other` (extensível).

### 2.2 Tabelas auxiliares
- **`entity_identifiers`** (`id`, `entity_id` FK CASCADE, `id_type`, `value`, `normalized_value`, `is_primary`, `metadata_json`, timestamps; índice `(id_type, normalized_value)`).
- **`entity_aliases`** (`id`, `entity_id` FK CASCADE, `name`, `normalized_name`, `alias_type`, timestamps).

### 2.3 Regras D1
Normalização para busca/correspondência. Duplicidades sugeridas de forma determinística (nome/alias/identificador) com motivos/nível, **sem fusão automática**. Mutações registram `audit_events` e `data_changes`.

## 3. D2 — Research & Evidence

### 3.1 `research_sources` (M1 `c1d2e3f4a5b6`)
Fonte de pesquisa/referência do dossiê (cadastro manual/determinístico). Campos: `name`, `source_type`, `domain`, `url`, `description`, `classification`, `consulted_at`, `last_verified_at`, `reliability_status`, `reliability_justification`, `verification_status`, `ingestion_source_id` (FK opcional `sources`, SET NULL), `metadata_json`, `created_by`, timestamps.

### 3.2 `documents` (estendida, M2 `d2e3f4a5b6c7`) e `document_entity_links`
Extensões: `document_type`, `description`, `origin_type`, `source_locator`, `occurred_at`, `captured_at`, `content_hash`, `verification_status`, `access_level`, `license_terms`, `is_reference_only`, `research_source_id` (FK opcional), timestamps; nulabilidades aditivas para cadastro manual com outras âncoras. **Invariante:** ao menos uma âncora/proveniência (`source_id`, `raw_record_id`, `research_source_id` ou `source_locator`). `document_entity_links` associa documento↔entidade (N:N).

### 3.3 `extracted_claims` (estendida, M3 `e3f4a5b6c7d8`) e `claim_entity_links`
Extensões: `entity_id`, `research_source_id`, `claim_origin`, `justification`, `registered_at`, `conflict_status`, `metadata_json` (e nulabilidade aditiva de `source_id` de ingestão). `claim_type`/`verification_status` explícitos; **sem promoção automática** de inferência/hipótese/previsão a fato verificado (marcação explícita com justificativa quando aplicável). `claim_entity_links` N:N (com `entity_id` principal mantido/sincronizado).

### 3.4 `claim_conflicts` (M4 `f4a5b6c7d8e9`)
Conflitos explícitos entre afirmações (`claim_id`, `conflicting_claim_id`, `conflict_type`, `description`, `status`, `detected_by`, `created_by`, timestamps), sem auto-conflito/par duplicado; recomputo determinístico de estado de conflito, **sem resolução automática**.

### 3.5 `evidence` (estendida, M5 `a5b6c7d8e9f0`)
Extensões: `document_id`, `research_source_id`, `evidence_type`, `relation_type` (`supports|contests|contextualizes`), `location_json`, `excerpt`, `updated_at` (nulabilidade aditiva de `source_id`). **Invariante:** ao menos uma âncora rastreável (documento, fonte de pesquisa, raw_record, source, localizador ou trecho/excerto).

## 4. D3 — Relationship History

### 4.1 `entity_interactions` (nova, M `b6c7d8e9f0a1`)
Histórico de interações por entidade (linha do tempo), distinto de D2 e sem uso de `relationships` (D4).

| Campo | Tipo | Notas |
|---|---|---|
| `id` | String(36), PK | UUID. |
| `entity_id` | String(36), FK `entities.id` CASCADE, not null, index | Entidade âncora. |
| `interaction_type` | String(100), not null, index | Tipo controlado na aplicação (ex.: reunião, chamada, e-mail, mensagem, evento, visita, nota etc.). |
| `title` | String(300), not null | Resumo curto. |
| `description` | Text, nullable | Contexto/detalhes. |
| `nature` | String(50), not null, index | **Obrigatória:** `declarado` \| `observado` \| `interpretado` \| `a_confirmar`. |
| `status` | String(50), not null, default `registered`, index | Estado do registro (ex.: `registered`, `confirmed`, `needs_review`, `contested`, `cancelled`, `archived`), atualizado explicitamente. |
| `occurred_at` | DateTime(tz), nullable, index | Instante principal (timeline). |
| `started_at` / `ended_at` | DateTime(tz), nullable | Intervalo opcional (validação `ended_at >= started_at`). |
| `time_precision` | String(30), nullable | `exact|date|month|approximate|unknown`. |
| `channel` | String(100), nullable | Canal/meio. |
| `location_text` | String(300), nullable | Local/contexto. |
| `participants_text` | Text, nullable | Participantes/partes de forma descritiva (sem criar relações D4). |
| `source_locator` | Text, nullable | URL/referência/localizador externo. |
| `document_id` | String(36), FK `documents.id` SET NULL, nullable | Proveniência documental opcional. |
| `research_source_id` | String(36), FK `research_sources.id` SET NULL, nullable | Fonte de pesquisa opcional. |
| `raw_record_id` | String(36), FK `raw_records.id` SET NULL, nullable | Proveniência de ingestão opcional. |
| `claim_id` | String(36), FK `extracted_claims.id` SET NULL, nullable | Afirmação relacionada opcional. |
| `evidence_id` | String(36), FK `evidence.id` SET NULL, nullable | Evidência relacionada opcional. |
| `confidence` | Float, nullable | Confiança declarada (0–1), nunca inferida. |
| `justification` | Text, nullable | Justificativa/observações. |
| `verification_status` | String(50), not null, default `nao_verificado` | Vocabulário de verificação existente. |
| `metadata_json` | JSON, nullable | Metadados controlados/extensíveis. |
| `created_by` | String(100), nullable | Ator. |
| `created_at` / `updated_at` | DateTime(tz), not null | Timestamps padrão. |

**Índices:** `entity_id`, `interaction_type`, `nature`, `status`, `occurred_at`, `(entity_id, occurred_at)`, `(entity_id, nature)`, `(entity_id, status)`.

### 4.2 Regras e invariantes D3
- `nature` explícita e obrigatória; `interpretado` e `a_confirmar` não representam fato confirmado e não são promovidos automaticamente.
- Atualizações de estado/verificação/natureza são explícitas e rastreáveis (recomendada justificativa para registros interpretados/pendentes e mudanças sensíveis).
- Validações determinísticas: entidade existente, vocabulários permitidos, coerência temporal (`ended_at >= started_at`), confiança em [0,1].
- **Integridade de referências opcionais:** referências fornecidas (`document_id`, `research_source_id`, `raw_record_id`, `claim_id`, `evidence_id`) devem existir quando informadas (validadas pelo serviço).
- Proveniência opcional por âncoras/localizador, sem derivação automática a partir de ingestão/afirmações/evidências.
- Mutações registram `audit_events` e `data_changes` (reuso de estruturas existentes).

## 5. Rastreabilidade e estados (transversal D1–D3)
- Mutações registram `audit_events` e `data_changes` (e `processing_events` em etapas determinísticas quando aplicável).
- Estados epistemológicos/verificação/confiabilidade/conflito são explícitos e atualizados por ações determinísticas; nenhuma inferência automática altera fatos/estados sem registro explícito.

## 6. Reuso existente (sem alteração estrutural de escopo)
- `entities`, `entity_identifiers`, `entity_aliases` (D1); estruturas D2; `raw_records`, `sources` de ingestão, `audit_events`, `data_changes`, `processing_events`.
- `relationships` **reservado a D4** (conexões entre entidades), não utilizado em D3.

## 7. Extensões previstas (D4–D5)
- D4: conexões entre entidades com temporalidade/evidências e visualização (uso de `relationships`).
- D5: insights estratégicos rastreáveis, sem execução automática.
- D6: consolidação/refinamento do módulo.
