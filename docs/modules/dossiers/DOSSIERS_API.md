# DOSSIERS — API (D1: Entity Profiles, D2: Research & Evidence)

Base: `/api/v1/dossiers` (local, loopback). Formato JSON. Mutações registram rastreabilidade (`audit_events`/`data_changes`, e `processing_events` quando aplicável). D2 é determinístico/manual-first, sem promoção automática de inferência a fato e sem coleta/integrações externas automáticas.

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
Registra documento/referência e associa à entidade (entidade do path garantida no vínculo).
- **Body:** `DocumentCreate` (`title?`, `document_type?`, `description?`, `origin_type?`, `source_locator?`, `mime_type?`, `storage_path?`, `checksum?`, `content_hash?`, `size_bytes?`, `language?`, `published_at?`, `occurred_at?`, `captured_at?`, `collected_at?`, `verification_status?`, `access_level?`, `license_terms?`, `is_reference_only`, `metadata_json?`, `source_id?`/ingestão, `raw_record_id?`, `research_source_id?`, `entity_ids?`, `entity_role?`).
- **201:** `DocumentDetail` (inclui `entity_links`). **404/422.**
- **Regra:** requer ao menos uma âncora de proveniência (`source_id`, `raw_record_id`, `research_source_id` ou `source_locator`).

### `GET /entities/{entity_id}/documents`
- **Query:** `q?`, `document_type?`, `verification_status?`, `origin_type?`, `sort?` (`updated_desc|created_desc|published_desc|title_asc`), `limit`, `offset`.
- **200:** `DocumentListResponse`.

### `GET /documents/{document_id}` | `PATCH /documents/{document_id}`
- **200:** `DocumentDetail`. **404/422.**

### `POST /documents/{document_id}/entities`
- **Body:** lista de `{ entity_id, role?, notes? }`. **200:** lista de vínculos criados/adicionados (sem duplicar par entidade/papel). **404/422.**

## D2 — Afirmações (claims)

### `POST /entities/{entity_id}/claims`
Cria afirmação manual/determinística vinculada à entidade.
- **Body:** `ClaimCreate` (`claim_text`, `claim_type?`, `claim_origin?`, `verification_status?`, `confidence?`, `justification?`, `source_id?`, `raw_record_id?`, `document_id?`, `research_source_id?`, `entity_ids?`, datas `published_at?/collected_at?/occurred_at?/valid_from?/valid_to?/registered_at?`, `structured_json?`, `metadata_json?`).
- **201:** `ClaimDetail` (com `entity_links`, `evidence`, `conflicts`). **404/422.**
- **Regras epistemológicas:** classificação e verificação explícitas; inferência/hipótese/previsão marcada como verificada requer justificativa explícita; sem promoção automática a fato.

### `GET /entities/{entity_id}/claims`
- **Query:** `q?`, `claim_type?`, `verification_status?`, `conflict_status?`, `sort?` (`updated_desc|created_desc|occurred_desc`), `limit`, `offset`.
- **200:** `ClaimListResponse`.

### `GET /claims/{claim_id}` | `PATCH /claims/{claim_id}`
- **200:** `ClaimDetail`. **404/422.**

## D2 — Conflitos entre afirmações

### `POST /claims/{claim_id}/conflicts`
- **Body:** `ClaimConflictCreate` (`conflicting_claim_id`, `conflict_type`, `description?`, `status?`).
- **201:** `ClaimConflictDetail`. **404/409/422** (ex.: par já existente, auto-conflito, afirmação inexistente).

### `PATCH /claims/{claim_id}/conflicts/{conflict_id}`
- **Body:** `ClaimConflictUpdate` (`conflict_type?`, `description?`, `status?`). **200:** `ClaimConflictDetail`. **404/422.**

### `GET /entities/{entity_id}/conflicts`
- **Query:** `status?`, `limit`, `offset`. **200:** `ClaimConflictListResponse`.

## D2 — Evidências

### `POST /claims/{claim_id}/evidence`
- **Body:** `EvidenceCreate` (`relation_type` `supports|contests|contextualizes`, `evidence_type?`, `document_id?`, `research_source_id?`, `source_id?`, `raw_record_id?`, `locator?`, `location_json?`, `snippet?`, `excerpt?`, `note?`, datas, `confidence?`, `verification_status?`).
- **201:** `EvidenceDetail`. **404/422.**
- **Regra:** requer ao menos uma âncora rastreável (documento, fonte de pesquisa, raw_record, source, localizador ou trecho/excerto).

### `GET /claims/{claim_id}/evidence`
- **200:** `EvidenceListResponse` (`items`, `total`, `limit`, `offset`).

### `GET /evidence/{evidence_id}` | `PATCH /evidence/{evidence_id}`
- **200:** `EvidenceDetail`. **404/422.**

## D2 — Research Workspace (resumo determinístico)

### `GET /entities/{entity_id}/research/summary`
- **200:** `ResearchSummaryResponse` `{ entity_id, documents_count, research_sources_count, claims_count, evidence_count, pending_verification_claims, open_conflicts, claims_by_type, claims_by_verification }` — indicadores derivados deterministicamente de dados persistidos. **404.**

## Fora de escopo (D2)
Sem fusão automática de entidades, sem endpoints de D3–D5, sem coleta/agentes automáticos, sem upload remoto/integrações comerciais obrigatórias e sem promoção automática de inferência a fato.
