# DOSSIERS — API (D1: Entity Profiles, D2: Research & Evidence, D3: Relationship History)

Base: `/api/v1/dossiers` (local, loopback). Formato JSON. Mutações registram rastreabilidade (`audit_events`/`data_changes`, e `processing_events` quando aplicável). Operação determinística/manual-first, sem promoção automática de inferência a fato, sem fusão automática e sem coleta/agentes/integrações externas automáticas.

## D1 — Entidades

### `POST /entities`
Cria entidade/perfil de dossiê.
- **Body:** `EntityCreate` — `entity_type`, `canonical_name`, `description?`, `profile_status?`, `primary_location?`, `verification_status?`, `confidence?`, `profile_data?`, `attributes_json?`, `source_first_id?`, `identifiers[]?`, `aliases[]?`.
- **201:** `EntityDetailResponse`. **422:** validação.

### `GET /entities`
Lista/pesquisa entidades.
- **Query:** `q?`, `entity_type?`, `profile_status?`, `verification_status?`, `updated_from?`, `updated_to?`, `sort?` (`updated_desc|updated_asc|created_desc|created_asc|name_asc`), `limit` (1–100, default 20), `offset`.
- **200:** `EntityListResponse { items, total, limit, offset }`.

### `GET /entities/{entity_id}`
- **200:** `EntityDetailResponse`. **404:** não encontrada.

### `PATCH /entities/{entity_id}`
- **Body:** `EntityUpdate` (parcial; substituição opcional de `identifiers`/`aliases` quando fornecidos).
- **200:** `EntityDetailResponse`. **404/422.**

### `GET /entities/{entity_id}/duplicate-candidates`
Sugestões de duplicidade (somente leitura, sem fusão).
- **Query:** `limit?` (default 10). **200:** `DuplicateCandidatesResponse`.

## D2 — Fontes de pesquisa

### `POST /research-sources`
- **Body:** `ResearchSourceCreate` (`name`, `source_type`, `domain?`, `url?`, `description?`, `classification?`, `consulted_at?`, `last_verified_at?`, `reliability_status?`, `reliability_justification?`, `verification_status?`, `ingestion_source_id?`, `metadata_json?`, `created_by?`).
- **201:** `ResearchSourceDetail`. **422:** validação.

### `GET /research-sources`
- **Query:** `q?`, `source_type?`, `classification?`, `reliability_status?`, `verification_status?`, `sort?` (`updated_desc|updated_asc|name_asc|consulted_desc|verified_desc`), `limit`, `offset`.
- **200:** `ResearchSourceListResponse`.

### `GET /research-sources/{source_id}` | `PATCH /research-sources/{source_id}`
- **200:** `ResearchSourceDetail`. **404/422.**

## D2 — Documentos

### `POST /entities/{entity_id}/documents`
Registra documento/referência e associa à entidade.
- **Body:** `DocumentCreate` (`title?`, `document_type?`, `description?`, `origin_type?`, `source_locator?`, `mime_type?`, `storage_path?`, `checksum?`, `content_hash?`, `size_bytes?`, `language?`, datas, `verification_status?`, `access_level?`, `license_terms?`, `is_reference_only`, `metadata_json?`, `source_id?`, `raw_record_id?`, `research_source_id?`, `entity_ids?`, `entity_role?`).
- **201:** `DocumentDetail`. **404/422.** Requer ao menos uma âncora de proveniência (`source_id`, `raw_record_id`, `research_source_id` ou `source_locator`).

### `GET /entities/{entity_id}/documents`
- **Query:** `q?`, `document_type?`, `verification_status?`, `origin_type?`, `sort?`, `limit`, `offset`. **200:** `DocumentListResponse`.

### `GET /documents/{document_id}` | `PATCH /documents/{document_id}`
- **200:** `DocumentDetail`. **404/422.**

### `POST /documents/{document_id}/entities`
- **Body:** lista de `{ entity_id, role?, notes? }`. **200:** vínculos criados/adicionados. **404/422.**

## D2 — Afirmações (claims)

### `POST /entities/{entity_id}/claims`
Cria afirmação manual/determinística vinculada à entidade.
- **Body:** `ClaimCreate` (`claim_text`, `claim_type?`, `claim_origin?`, `verification_status?`, `confidence?`, `justification?`, proveniências/datas opcionais, `structured_json?`, `metadata_json?`, `entity_ids?`).
- **201:** `ClaimDetail`. **404/422.**
- **Regras:** classificação/verificação explícitas; inferência/hipótese/previsão marcada como verificada requer justificativa explícita; sem promoção automática a fato.

### `GET /entities/{entity_id}/claims`
- **Query:** `q?`, `claim_type?`, `verification_status?`, `conflict_status?`, `sort?`, `limit`, `offset`. **200:** `ClaimListResponse`.

### `GET /claims/{claim_id}` | `PATCH /claims/{claim_id}`
- **200:** `ClaimDetail`. **404/422.**

## D2 — Conflitos entre afirmações

### `POST /claims/{claim_id}/conflicts`
- **Body:** `ClaimConflictCreate` (`conflicting_claim_id`, `conflict_type`, `description?`, `status?`).
- **201:** `ClaimConflictDetail`. **404/409/422.**

### `PATCH /claims/{claim_id}/conflicts/{conflict_id}`
- **Body:** `ClaimConflictUpdate`. **200:** `ClaimConflictDetail`. **404/422.**

### `GET /entities/{entity_id}/conflicts`
- **Query:** `status?`, `limit`, `offset`. **200:** `ClaimConflictListResponse`.

## D2 — Evidências

### `POST /claims/{claim_id}/evidence`
- **Body:** `EvidenceCreate` (`relation_type` `supports|contests|contextualizes`, `evidence_type?`, âncoras opcionais `document_id?`/`research_source_id?`/`source_id?`/`raw_record_id?`, `locator?`, `location_json?`, `snippet?`, `excerpt?`, `note?`, datas, `confidence?`, `verification_status?`).
- **201:** `EvidenceDetail`. **404/422.** Requer ao menos uma âncora rastreável.

### `GET /claims/{claim_id}/evidence`
- **200:** `EvidenceListResponse`.

### `GET /evidence/{evidence_id}` | `PATCH /evidence/{evidence_id}`
- **200:** `EvidenceDetail`. **404/422.**

## D2 — Research Workspace (resumo determinístico)

### `GET /entities/{entity_id}/research/summary`
- **200:** `ResearchSummaryResponse` (contagens e distribuições derivadas deterministicamente de dados persistidos). **404.**

## D3 — Relationship History (interações/timeline)

> D3 registra interações ao longo do tempo (distinto de D2) e não utiliza `relationships` (reservado a D4). Natureza explícita e obrigatória; sem promoção automática a fato.

### `POST /entities/{entity_id}/interactions`
Cria interação vinculada à entidade.
- **Body:** `InteractionCreate` — `interaction_type` (obrigatório), `title` (obrigatório), `nature` (obrigatória: `declarado|observado|interpretado|a_confirmar`), `description?`, `status?` (default `registered`), `occurred_at?`, `started_at?`, `ended_at?`, `time_precision?`, `channel?`, `location_text?`, `participants_text?`, `source_locator?`, `document_id?`, `research_source_id?`, `raw_record_id?`, `claim_id?`, `evidence_id?`, `confidence?` (0–1), `justification?`, `verification_status?`, `metadata_json?`, `created_by?`.
- **201:** `InteractionDetail`. **404:** entidade ou referência opcional inexistente. **422:** validação (natureza/tipo/título, coerência temporal, confiança etc.).

### `GET /entities/{entity_id}/interactions`
Lista/timeline de interações da entidade.
- **Query:** `q?` (busca em título/descrição/canal/participantes/local), `interaction_type?`, `nature?`, `status?`, `date_from?`, `date_to?`, `sort?` (`occurred_desc` default, `occurred_asc`, `created_desc`, `created_asc`), `limit` (1–100, default 20), `offset`.
- **200:** `InteractionListResponse { items, total, limit, offset }`. **404:** entidade inexistente.

### `GET /interactions/{interaction_id}`
- **200:** `InteractionDetail`. **404:** não encontrada.

### `PATCH /interactions/{interaction_id}`
Atualização parcial/ajuste explícito de estado, natureza, verificação e demais campos (rastreável).
- **Body:** `InteractionUpdate` (campos parciais).
- **200:** `InteractionDetail`. **404:** interação ou referência opcional inexistente. **422:** validação.

### `GET /entities/{entity_id}/interactions/summary`
Resumo determinístico derivado de dados persistidos.
- **200:** `InteractionSummaryResponse` `{ entity_id, interactions_count, pending_confirmation_or_review, by_nature, by_type, by_status, earliest_occurred_at, latest_occurred_at }`. **404:** entidade inexistente.

## Fora de escopo (D1–D3)
- Fusão automática de entidades; endpoints D4–D6; uso/definição de `relationships` (D4).
- Coleta/agentes automáticos, derivação/importação automática de interações, upload remoto ou integrações comerciais/APIs pagas obrigatórias.
- Promoção automática de inferências/hipóteses/previsões a fato.
