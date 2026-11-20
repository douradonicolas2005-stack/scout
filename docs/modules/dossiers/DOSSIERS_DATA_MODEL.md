# DOSSIERS — Modelo de Dados (D1: Entity Profiles, D2: Research & Evidence)

> **D1:** migração `b7d1e2f3a4c5` (`dossiers_d1_entity_profiles`, down de `426757a848bb`).  
> **D2:** migrações aditivas em cadeia `c1d2e3f4a5b6` → `d2e3f4a5b6c7` → `e3f4a5b6c7d8` → `f4a5b6c7d8e9` → `a5b6c7d8e9f0` (após `b7d1e2f3a4c5`).  
> **Banco:** SQLite/Alembic. Extensões D2 validadas em migração de banco temporário (`alembic upgrade head`), sem alteração automática do DB local nesta etapa.

## 1. Princípios de reuso
- **`entities`** permanece a entidade canônica do dossiê (não duplicada). D1 estende `entities` e adiciona identificadores/aliases; D2 associa documentos e afirmações às entidades sem recriar perfil.
- Reuso de proveniência/rastreabilidade transversais: `audit_events`, `data_changes`, `processing_events` (etapas determinísticas), e referência opcional a estruturas de ingestão Foundation (`sources` operacionais, `raw_records`) quando aplicável.
- **Separação semântica:** `sources` (Source Registry/ingestão operacional) ≠ `research_sources` (fontes de pesquisa/referência do dossiê, cadastro manual/consultivo). Documentos/afirmações/evidências podem referenciar proveniências de ingestão e/ou pesquisa, sem promoção automática de inferência a fato.

## 2. D1 — Entity Profiles

### 2.1 Alterações em `entities` (aditivas)
| Coluna | Tipo | Notas |
|---|---|---|
| `description` | Text, nullable | Descrição curta para cabeçalho do dossiê. |
| `profile_status` | String(50), not null, default `active`, index | Estado cadastral do perfil, distinto de verificação. |
| `primary_location` | String(300), nullable | Localização em nível apropriado. |
| `profile_data` | JSON, nullable | Atributos por tipo de entidade e metadados de cadastro. |

Campos existentes preservados (`entity_type`, `canonical_name`, `normalized_name`, `attributes_json`, confiança/verificação/proveniência temporal etc.).

### 2.2 Tabelas auxiliares
- **`entity_identifiers`** (`id`, `entity_id` FK CASCADE, `id_type`, `value`, `normalized_value`, `is_primary`, `metadata_json`, timestamps; índice `(id_type, normalized_value)`).
- **`entity_aliases`** (`id`, `entity_id` FK CASCADE, `name`, `normalized_name`, `alias_type`, timestamps).

### 2.3 Regras D1
Tipos suportados `person|company|economic_group|institution|other` (extensível). Normalização para busca/correspondência. Duplicidades sugeridas de forma determinística (nome/alias/identificador) com motivos/nível, **sem fusão automática**. Mutações registram `audit_events` e `data_changes`.

## 3. D2 — Research & Evidence

### 3.1 `research_sources` (nova, M1 `c1d2e3f4a5b6`)
Fonte de pesquisa/referência do dossiê (catálogo local, cadastro manual/determinístico).
- Campos principais: `id` (PK), `name`, `source_type`, `domain`, `url`, `description`, `classification`, `consulted_at`, `last_verified_at`, `reliability_status` (default `nao_avaliada`), `reliability_justification`, `verification_status` (default `nao_verificado`), `ingestion_source_id` (FK opcional `sources.id`, SET NULL), `metadata_json`, `created_by`, timestamps.
- Finalidade: registrar procedência de consulta, classificação e confiabilidade/justificativa sem depender de configuração operacional de coleta.

### 3.2 `documents` (estendida, M2 `d2e3f4a5b6c7`)
Extensão aditiva da tabela Foundation para suportar registro/consulta de documentos e referências no dossiê.
- Extensões: `document_type`, `description`, `origin_type` (default `manual`), `source_locator`, `occurred_at`, `captured_at`, `content_hash`, `verification_status` (default `nao_verificado`), `access_level`, `license_terms`, `is_reference_only` (default `false`), `research_source_id` (FK opcional `research_sources.id`, SET NULL), `created_at`/`updated_at`.
- Ajustes de compatibilidade (SQLite): nulabilidade aditiva de `source_id` (ingestão) e `collected_at` para permitir cadastro manual com outras âncoras de proveniência.
- Invariantes de aplicação: ao menos uma âncora/proveniência (`source_id`, `raw_record_id`, `research_source_id` ou `source_locator`); hash/integridade registrado quando aplicável a cópia local controlada; respeito a referência-only/licença/permissão no fluxo determinístico.

### 3.3 `document_entity_links` (nova, M2)
Associação N:N documento↔entidade.
- Campos: `id`, `document_id` (FK CASCADE), `entity_id` (FK CASCADE), `role`, `notes`, `created_at`; índice único lógico `(document_id, entity_id, role)`.

### 3.4 `extracted_claims` (estendida, M3 `e3f4a5b6c7d8`)
Afirmações registradas (prioridade manual/determinística) com epistemologia e proveniência explícitas.
- Extensões: `entity_id` (FK opcional `entities.id`), `research_source_id` (FK opcional), `claim_origin` (default `manual`), `justification`, `registered_at`, `conflict_status` (default `none`), `metadata_json`.
- Ajuste de compatibilidade: nulabilidade aditiva de `source_id` de ingestão.
- Regras: `claim_type` (declaração/fato_verificado/inferência/hipótese/previsão/desconhecido) e `verification_status` explícitos; **sem promoção automática** de inferência/hipótese/previsão a fato verificado — marcação explícita com justificativa quando aplicável.

### 3.5 `claim_entity_links` (nova, M3)
Associação N:N afirmação↔entidade (com `entity_id` principal mantido em `extracted_claims` para consulta/compatibilidade, sincronizado pelo serviço).
- Campos: `id`, `claim_id` (FK CASCADE), `entity_id` (FK CASCADE), `relevance`, `created_at`; índice único `(claim_id, entity_id)`.

### 3.6 `claim_conflicts` (nova, M4 `f4a5b6c7d8e9`)
Registro explícito e rastreável de contradições/conflitos entre afirmações (sem resolução automática).
- Campos: `id`, `claim_id` (FK `extracted_claims` CASCADE), `conflicting_claim_id` (FK CASCADE), `conflict_type`, `description`, `status` (default `open`: `open|under_review|resolved|dismissed`), `detected_by` (default `user`), `created_by`, timestamps.
- Restrições/invariantes: sem auto-conflito, par normalizado único (ordem independente). Estado de conflito das afirmações afetadas recomputado de forma determinística (`none|contested/conflicting|under_review` conforme implementação do serviço).

### 3.7 `evidence` (estendida, M5 `a5b6c7d8e9f0`)
Evidências vinculadas a afirmações com papel e ancoragem rastreável.
- Extensões: `document_id` (FK opcional `documents.id`), `research_source_id` (FK opcional), `evidence_type`, `relation_type` (default `supports`: `supports|contests|contextualizes`), `location_json`, `excerpt`, `updated_at`.
- Ajuste de compatibilidade: nulabilidade aditiva de `source_id` de ingestão.
- Invariantes de aplicação: evidência deve referenciar ao menos uma âncora rastreável (documento, fonte de pesquisa, raw_record, source, localizador ou trecho/excerto).

## 4. Rastreabilidade e estados
- Mutações D2 registram `audit_events` e `data_changes` (e `processing_events` em etapas determinísticas quando aplicável, ex.: registro de documento).
- Estados epistemológicos/verificação/confiabilidade/conflito são explícitos e atualizados por ações determinísticas; nenhuma inferência automática altera fatos/estados sem registro explícito.

## 5. Reuso existente (sem alteração estrutural D2)
- `entities`, `entity_identifiers`, `entity_aliases` (D1), `raw_records`, `sources` de ingestão, `audit_events`, `data_changes`, `processing_events`.
- `relationships` permanece reservado a D4 (conexões entre entidades), não utilizado para conflitos entre afirmações.

## 6. Extensões previstas (D3–D5)
- D3: histórico/linha do tempo de interações (distinto de histórico de pesquisa/evidências D2).
- D4: conexões entre entidades com temporalidade/evidências e visualização.
- D5: insights estratégicos rastreáveis, sem execução automática.
