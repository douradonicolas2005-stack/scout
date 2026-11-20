# D4 — Connections: Planejamento Técnico Final (congelado para implementação)

> **Módulo:** Dossiers · **Subetapa:** D4 Connections (relações entre entidades)  
> **Status:** planejamento técnico final, coerente e implementável (documentação), **não implementado** (sem código, sem migrações, sem alterações de banco, sem dependências, sem commit/push)  
> **Base:** Foundation V1.1 + D1–D3 publicados (`main@a081db4`, Alembic head `b6c7d8e9f0a1`)  
> **Princípios:** local-first (loopback), determinístico/manual-first, rastreável, epistemologia explícita, controle humano, sem promoção automática a fato, sem inferência/fusão/derivação automática, sem simulação de dados/UI/cenários, sem agentes/coleta automática, sem dependências pagas/comerciais/serviços externos, sem paralelismo pesado.

Este documento encerra o fechamento arquitetural de D4, incorporando as decisões pendentes, os ajustes semânticos adicionais solicitados e o **último ajuste de fechamento** (restrição semântica dos tipos de entidade por relação, especialmente `other`), e congela o planejamento para revisão e aprovação explícita antes de qualquer implementação. **Nenhuma execução de D4 foi iniciada.**

## Decisões preservadas (inalteradas)

- **Reutilização exclusiva da tabela `relationships`** da Foundation. **Nenhuma segunda estrutura/tabela de relações.**
- **Migração Alembic exclusivamente aditiva**, filha de `b6c7d8e9f0a1`. Nenhuma alteração destrutiva em Foundation, D1, D2 ou D3.
- **Direcionalidade limitada a `directed` e `undirected`** no MVP. **`bidirectional` fora do MVP.**
- **Natureza, verificação e estado como dimensões separadas** e explícitas.
- **`confidence` opcional e nullable** (nunca obrigatória quando não houver fundamento).
- **Nenhuma promoção automática de inferência a fato verificado.** Nenhuma criação automática de relações a partir de Claims, Evidences ou Interactions (ou de heurísticas/padrões/inferências).
- **Proveniência por reuso de `claim_id` e `evidence_id`** (cadeia D2), sem duplicação redundante de conteúdo probatório.
- **Arquivamento e inativação como política primária. Sem hard delete no fluxo da interface do MVP.**
- **Visualização principal:** lista estruturada. **Grafo Cytoscape.js simples e complementar**, condicionado à viabilidade técnica (fallback obrigatório para lista/filtros/detalhe/navegação), sobre relações reais cadastradas (sem simulação).
- **Sem implementação de D5. Sem simulação de cenários/previsões.** Arquitetura local-first, sem serviços externos pagos ou dependências desnecessárias.

## Resolução das decisões e ajustes incorporados (fechamento)

| Item | Decisão final incorporada |
|---|---|
| Duplicidade semântica | **HTTP 409 Conflict** para duplicidade semântica/conflito com relação existente (incluindo equivalências e conflitos temporais definidos); **422** para dados inválidos/incompatibilidades/violações de validação; **404** para entidade/referência inexistente. Validação determinística e transacional. |
| Granularidade temporal | **Modelo temporal atual mantido no MVP** (`occurred_at`, `valid_from`, `valid_to`, `time_precision` com vocabulário `exact|month|year|estimated|unknown`), sem novas estruturas/alterações silenciosas; limitação de `DateTime` + precisão única documentada; evolução futura para granularidade por campo registrada (não implementada). |
| Vigências múltiplas | Permitidas para o **mesmo vínculo semântico** em **períodos históricos efetivamente distintos** (não equivalentes e não sobrepostos de forma incompatível), preservando histórico; períodos equivalentes e sobreposições incompatíveis rejeitados como conflito (409), sem correção automática. |
| Reativação de arquivados | **Arquivados não são reativados diretamente no MVP.** Vínculo restabelecido/novamente identificado ⇒ **novo registro** com nova vigência, preservando registro anterior e rastreabilidade, respeitando regras de duplicidade/temporalidade. |
| Grafo Cytoscape.js | Incluído como **componente complementar planejado para o MVP, condicionado à viabilidade técnica**, com requisitos definidos; lista permanece principal; grafo não bloqueia MVP (fallback obrigatório). |
| `created_by` e legados | Formato controlado `<actor_type>:<actor_id>` (`human_user|ai_agent|internal_process`); **novos registros D4 exigem autoria identificada**; `NULL` apenas para legados/compatibilidade explicitamente justificada (leitura defensiva); sem sistema de identidade dedicado; sem criação automática por agentes em D4. |
| Governança de pares inversos | Pares inversos **formalizados semanticamente** e documentados no catálogo; equivalência ≠ igualdade literal de ID; normalização de perspectiva para evitar dois registros do mesmo vínculo; tipos apenas semelhantes não conflitam; novos pares/históricos exigem revisão humana (sem fusão/correção automática). `biz.supplier_to` ↔ `biz.customer_of` preservado; `corp.subsidiary_of` **não** incluído no MVP. |
| Catálogo operacional congelado | Catálogo revisado e congelado com status por tipo (`approved`, `deferred`, `blocked_by_model`, `requires_review`), tabela consolidada final e critérios de habilitação; tipos não representáveis corretamente com entidades D1 não habilitados no MVP. |
| Ajustes semânticos adicionais | `corp.partner_in_vehicle` não habilitado no MVP (identidade do veículo não representável adequadamente; sem nova estrutura). `asset.owner_of` documentado como futuro e não habilitado no MVP (sem tipo de entidade “ativo” em D1). `corp.beneficial_owner_of` mantido com distinções/restrições estritas e sem criação automática (habilitação operacional condicionada a revisão/aprovação explícita de critérios). `exec.advisor_to` definido como assessoria profissional sem presunção de vínculo empregatício/societário/cargo executivo/exclusividade. |
| **Permissividade do tipo `other` (ajuste final)** | **Tipos de entidade por relação restringidos por compatibilidade semântica.** `other` não é permitido no catálogo congelado do MVP por ausência de justificativa semântica suficiente (evita registros semanticamente inadequados e preserva a qualidade do grafo). Relações familiares e executivas restritas a entidades compatíveis; tipos patrimoniais aprovados revisados para especificidade (estruturas/veículos representados como entidades D1). **A validação da API/serviço aplicará efetivamente essas restrições (422 em incompatibilidade).** |

---

## 1. Modelo de dados

### 1.1 Estrutura e estratégia de evolução
- **Tabela:** reutilizar exclusivamente `relationships` (Foundation). **Nenhuma segunda estrutura de relações.**
- **Migração:** Alembic **aditiva**, filha de `b6c7d8e9f0a1` (ex.: `d4_connections`). Sem alterações destrutivas, sem renomeações/remoções de colunas existentes.
- **Compatibilidade:** defaults/nullable seguros para linhas legadas; leitura defensiva quando necessário. `relationships` legadas devem permanecer legíveis.

### 1.2 Campos existentes preservados (inalterados em semântica/base)

| Campo | Tipo (Foundation atual) | Nulo | Decisão D4 |
|---|---|---|---|
| `id` | String(36) PK | não | Preservado (UUID). |
| `from_entity_id` | String(36) FK `entities.id` (CASCADE), index | não | Preservado. Para `directed`: origem semântica. Para `undirected`: **extremo canônico A** (§3). |
| `to_entity_id` | String(36) FK `entities.id` (CASCADE), index | não | Preservado. Para `directed`: destino semântico. Para `undirected`: **extremo canônico B** (§3). |
| `relation_type` | String(100), index | não | Preservado; deve conter **apenas ID estável** da taxonomia operacional congelada (§2). Texto livre rejeitado. |
| `attributes_json` | JSON | sim | Preservado para metadados extensíveis/compatibilidade; **não** substitui campos tipados normativos de D4. |
| `claim_id` | String(36) FK `extracted_claims.id` (SET NULL) | sim | Preservado. Vínculo probatório D2 opcional (§7). |
| `evidence_id` | String(36) FK `evidence.id` (SET NULL) | sim | Preservado. Vínculo probatório D2 opcional (§7). |
| `confidence` | Float | sim | Preservado, **opcional/nullable** (§5). |
| `verification_status` | String(50), default `nao_verificado` | não | Preservado; D4 restringe vocabulário em escrita/leitura operacional (§5). |
| `occurred_at` | DateTime(tz) | sim | Preservado. Semântica formalizada em §6. |
| `valid_from` | DateTime(tz) | sim | Preservado. Semântica formalizada em §6. |
| `valid_to` | DateTime(tz) | sim | Preservado. Semântica formalizada em §6. |
| `created_at` | DateTime(tz) | não | Preservado (mixin). |
| `updated_at` | DateTime(tz) | não | Preservado (mixin). |

**FKs/restrições existentes mantidas:** `entities` `ON DELETE CASCADE`; `extracted_claims`/`evidence` `ON DELETE SET NULL`. Índices existentes mantidos.

### 1.3 Novos campos necessários (migração aditiva)

Todos aditivos, com defaults/nullable seguros para retrocompatibilidade.

| Campo | Tipo proposto | Nulo / Default | Finalidade |
|---|---|---|---|
| `directionality` | String(20) | não, default `directed` | `directed`/`undirected`. **Compatível com a taxonomia do `relation_type`** (§2, §3); default compatível com legados. |
| `nature` | String(30) | não, default `declarado` | Dimensão epistemológica explícita (§5). |
| `status` | String(30) | não, default `active`, index | Estado do registro (§5). |
| `description` | Text | sim | Descrição/contexto legível informado explicitamente. |
| `justification` | Text | sim | Fundamentação de registro/revisão/contestação; suporte à rastreabilidade, epistemologia e exceções temporais explicitamente justificadas (§4, §6). |
| `source_locator` | Text | sim | Localizador textual direto opcional (URL, referência, citação curta, caminho); complementar, não substitui evidência formal (§7). |
| `time_precision` | String(30) | sim | Precisão temporal controlada D4: `exact|month|year|estimated|unknown` (§6). |
| `created_by` | String(100) | sim (compatibilidade/legado; ver regra) | Autoria controlada de criação (§7); para **novos registros D4 obrigatório** em formato controlado. |

**Campos deliberadamente não adicionados:** `role_from`/`role_to`, `inverse_relation_type` persistido, `bidirectional`, FKs diretas D2 redundantes (`document_id`, `research_source_id`, `raw_record_id`, `source_id` operacional), cópia de conteúdo probatório, identificador livre de tipo, campos de granularidade temporal por campo, campos de identidade/usuário/agente dedicados. Papéis/rótulos inversos são **derivados** da taxonomia; metadados de equivalência inversa vivem no **contrato de taxonomia** (§2, §4).

### 1.4 Campos evitados por redundância com D2

| Candidato evitado | Motivo |
|---|---|
| `document_id`, `research_source_id`, `raw_record_id` (FKs diretas) | Cadeia probatória acessível via `claim_id`/`evidence_id` e vínculos D2; evita fontes de verdade concorrentes. |
| `source_id` operacional na relação | Proveniência operacional pertence a artefatos de ingestão/D2. |
| `snippet`/`excerpt`/conteúdo copiado | Pertencem a evidence/document; relação referencia, não duplica. |
| Identificador textual livre de relação | `relation_type` (ID estável) é a chave; exibição deriva da taxonomia. |
| Flag `is_inferred` separada | Redundante com `nature = inferido`. |

### 1.5 Índices e restrições (aditivos, propostos)

- **Preservar:** índices existentes (`from_entity_id`, `to_entity_id`, `relation_type`).
- **Adicionar (migração aditiva):** `status`, `nature`, `verification_status` (conforme filtro) e compostos para consulta/validação e suporte a checagens determinísticas:
  - `(from_entity_id, status)`, `(to_entity_id, status)`
  - `(from_entity_id, relation_type)`, `(to_entity_id, relation_type)`
  - `(from_entity_id, to_entity_id, relation_type, directionality)` (suporte à detecção de duplicidade/normalização; autoridade da regra semântica/temporal permanece no serviço, dado limites de unicidade parcial no SQLite).
- **Validações de domínio (serviço; CHECK quando viável):** `from_entity_id <> to_entity_id` (MVP), `directionality IN ('directed','undirected')`, vocabulários permitidos de `nature`/`status`/`verification_status`/`time_precision`, `confidence IS NULL OR (0 <= confidence <= 1)`, coerência temporal `valid_to >= valid_from` quando ambos presentes, `relation_type` existente e **aprovado/operacional** na taxonomia congelada (§2), compatibilidade `relation_type`↔`directionality`, **tipos de entidade origem/destino permitidos pelo tipo conforme taxonomia congelada** (aplicados efetivamente pelo serviço), `created_by` em formato controlado para novos registros D4 (§7).

### 1.6 Política de integridade referencial e validação

| Regra | Política | Erro |
|---|---|---|
| Entidades | `from_entity_id` e `to_entity_id` devem existir em `entities`. | 404 se inexistente |
| Auto-relação | **Proibida no MVP** (`from == to`). | 422 |
| Tipo operacional | `relation_type` deve existir na taxonomia e estar habilitado para operação no MVP (`status_mvp = approved`). Tipos não aprovados/indisponíveis/bloqueados/requerendo revisão não podem ser usados em novos registros. | 422 |
| Direcionalidade | `directionality` deve ser **exatamente** a declarada pelo tipo (se informada) ou derivada da taxonomia (se omitida). | 422 se incompatível |
| Tipos de entidade por relação | Tipos de `from`/`to` (com base em `entity_type` de D1) devem ser **semanticamente compatíveis** e constar nos conjuntos permitidos pelo `relation_type` na taxonomia congelada. **A API e o serviço aplicarão efetivamente essas restrições** (incluindo a vedação de `other` quando não houver justificativa semântica documentada no tipo). | 422 |
| Vocabulários/campos | `nature`, `verification_status`, `status`, `directionality`, `time_precision` e formatos controlados válidos. | 422 |
| Claim/Evidence | Se informados, devem existir. Se ambos informados, evidência deve ser coerente com o claim quando aplicável. | 404 inexistente; 422 incoerente |
| Temporal | `valid_to >= valid_from` quando ambos presentes; sem invenção de precisão ausente (§6). | 422 |
| Canonicidade/equivalência | `undirected` normalizado canonicamente; pares inversos equivalentes normalizados por semântica do vínculo (§3, §4). | — (base para 409) |
| Autoria (novos D4) | `created_by` obrigatório e em formato controlado para novos registros D4; `NULL` apenas legado/compatibilidade explicitamente justificada (não para criação D4). | 422 |
| Mutabilidade | Alterações sensíveis (extremos, tipo, natureza, verificação, status, vínculos, temporalidade) explícitas e rastreáveis; nenhuma mutação implícita. | — |

### 1.7 Política de exclusão, arquivamento e ciclo de vida

| Ação | Política |
|---|---|
| **Arquivamento** (preferencial) | `status = archived` por ação explícita e rastreável. Registro preservado para consulta/auditoria; excluído de visões ativas por padrão. |
| **Reativação de arquivado (MVP)** | **Não permitida diretamente.** Para vínculo restabelecido ou novamente identificado em período posterior: criar **novo registro** com nova vigência, preservando o anterior e a rastreabilidade, respeitando regras de duplicidade/temporalidade (§4, §6). Nenhuma alteração silenciosa do histórico. |
| **Inativação** | `status = inactive` para relação cessada/não vigente, mantendo histórico (distinto de arquivado). |
| **Exclusão física (hard delete)** | **Não exposta no MVP/UI.** Apenas operação administrativa excepcional fora do escopo de UI, com rastreabilidade e confirmação explícita, para erro de cadastro inequívoco (não recomendada). |
| **Cascatas/efeitos de FK** | Remoção administrativa de entidade → `CASCADE` em relações (comportamento Foundation preservado; sem fusão/exclusão automática promovida por D4). Remoção de claim/evidence → `SET NULL` no vínculo probatório, preservando a relação. |
| **Soft delete** | Sem `deleted_at`; `archived`/`inactive` são a forma canônica de retenção controlada. |

**Distinção normativa:**
- `inactive`: relação que deixou de estar vigente (cessada), preservada no histórico.
- `archived`: registro retirado do conjunto operacional, preservado para auditoria/histórico (não reativado diretamente).
- **Nova relação/novo registro:** vínculo restabelecido ou novamente identificado em período posterior (nova vigência/ocorrência), criado como registro distinto conforme regras.

---

## 2. Taxonomia operacional congelada

### 2.1 Princípios, governança e status de catálogo
- **Identificadores estáveis:** `relation_type` é ID imutável (string), usado em persistência/API/filtros. **Texto livre não é identificador.** Rótulos/descrições são metadados de apresentação/semântica associados ao ID.
- **Fonte de verdade:** catálogo determinístico versionável (código/configuração controlada) da taxonomia D4.
- **Categorias:** Societária, Executiva, Familiar, Empresarial, Institucional, Patrimonial.
- **Extensibilidade controlada:** novos tipos recebem **novo ID estável** (nunca reutilizar/renomear ID existente). Mudança semântica exige novo ID. Depreciação mantém leitura de históricos.
- **Sem expansão desnecessária.** Tipos não representáveis corretamente com entidades existentes em D1 **não** são habilitados no MVP.
- **Qualidade semântica do grafo (restrição de `other`):** o tipo de entidade `other` (existente em D1) **não representa categoria semântica suficientemente específica** para, em regra, sustentar relações de alta qualidade. Por isso, `other` **somente deve ser permitido** como origem/destino em um tipo de relação quando houver **justificativa semântica documentada e explícita** no próprio tipo. **No catálogo operacional congelado do MVP, nenhum tipo (aprovado, em revisão ou bloqueado) admite `other` em origem ou destino**, evitando registros tecnicamente válidos porém semanticamente inadequados (ex.: entidade genérica como familiar, diretora, acionista ou contraparte patrimonial).

**Status de tipo no planejamento/MVP (congelamento):**
- `approved`: aprovado para uso operacional no MVP (implementável com entidades/modelo atuais e regras definidas).
- `deferred`: documentado, mas temporariamente indisponível no MVP (adiado).
- `blocked_by_model`: depende de evolução futura do modelo de entidades/representação; não habilitado no MVP.
- `requires_review`: exige decisão humana adicional antes de habilitação operacional.

Somente tipos `approved` são utilizáveis em novos registros D4. Tipos com outros status permanecem documentados, porém **não operacionais** no MVP (422 se tentativa de uso).

### 2.2 Metadados obrigatórios por tipo operacional

Cada tipo **aprovado/operacional** deve declarar: `id` estável, nome de apresentação, definição semântica, direcionalidade (`directed`/`undirected`, fixa), tipos de entidade permitidos na origem, tipos de entidade permitidos no destino (semanticamente compatíveis), rótulo direto/simétrico e rótulo inverso (quando aplicável), papéis (quando aplicável), equivalência com outros tipos (`inverse_type_id`) quando aplicável, e restrições/ambiguidades. Tipos não operacionais devem registrar motivo/limitação e dependência.

**Tipos de entidade base (D1, existentes):** `person`, `company`, `economic_group`, `institution`, `other` (extensível apenas por evolução futura controlada). O planejamento **não inventa** tipos de entidade inexistentes. A utilização de `other` em relações é controlada pela taxonomia e, no MVP congelado, vedada por ausência de justificativa semântica documentada.

### 2.3 Tabela consolidada do catálogo (todos os tipos inicialmente propostos)

| ID | Categoria | Direcionalidade | Origem permitida | Destino permitido | Status MVP | Observações |
|---|---|---|---|---|---|---|
| `corp.shareholder_of` | Societária | `directed` | `person`, `company`, `economic_group`, `institution` | `company`, `economic_group`, `institution` | `approved` | Participação societária (ação/quota/participação) declarada/observada. Inverso: “Tem como acionista”. Distingue-se de titularidade patrimonial e não cria beneficiário final automaticamente; sem inferência. Origem/destino restritos a entidades semanticamente compatíveis em D1 (sem `other`). |
| `corp.parent_company_of` | Societária | `directed` | `company`, `economic_group`, `institution` | `company`, `economic_group`, `institution` | `approved` | Relação de controle/controladora sobre controlada no escopo registrado. Inverso: “Controlada por”. `corp.subsidiary_of` não incluído no MVP. Sem inferência de controle indireto. Sem `other`. |
| `corp.beneficial_owner_of` | Societária | `directed` | `person` | `company`, `economic_group`, `institution` | `requires_review` | Beneficiário final (UBO) de entidade/estrutura, distinto de proprietário formal/titular registral e de participação direta/controle indireto. **Não habilitar operacionalmente sem confirmação humana explícita** dos critérios: registro explícito, evidência apropriada e classificação epistemológica explícita; **proibida criação automática** a partir de participação indireta, controle presumido ou inferências. Tipos propostos restritos para precisão semântica (sem `other`); manter não operacional no MVP. |
| `corp.partner_in_vehicle` | Societária | `undirected` | `person`, `company`, `economic_group`, `institution` | `person`, `company`, `economic_group`, `institution` | `blocked_by_model` | **Não habilitado no MVP.** Coparticipação entre participantes não representável corretamente sem identificar o veículo envolvido. Modelar participante↔veículo por relação dirigida quando aplicável (ex.: `corp.shareholder_of`), sem presumir veículo. Evolução futura necessária; sem nova estrutura. Sem `other`. |
| `exec.director_of` | Executiva | `directed` | `person` | `company`, `economic_group`, `institution` | `approved` | Pessoa no exercício de função de direção em organização. Inverso: “Tem como diretor”. Não presume participação societária. Restrito a entidades semanticamente compatíveis (sem `other`). |
| `exec.officer_of` | Executiva | `directed` | `person` | `company`, `economic_group`, `institution` | `approved` | Pessoa em vínculo executivo/oficial (officer) junto à organização. Inverso: “Tem como executivo”. Sem `other`. |
| `exec.board_member_of` | Executiva | `directed` | `person` | `company`, `economic_group`, `institution` | `approved` | Pessoa membro de conselho/órgão colegiado da organização. Inverso: “Tem como conselheiro”. Não implica gestão executiva diária. Restrito a entidades semanticamente compatíveis (sem `other`). |
| `exec.advisor_to` | Executiva | `directed` | `person`, `company`, `institution` | `person`, `company`, `economic_group`, `institution` | `approved` | **Relação profissional de aconselhamento/assessoria.** Inverso: “Assessorado por”. **Sem pressupor** vínculo empregatício, participação societária, cargo executivo ou exclusividade profissional. Relações de outra natureza devem usar tipo próprio. Sem `other`. |
| `exec.employee_of` | Executiva | `directed` | `person` | `company`, `economic_group`, `institution` | `approved` | Pessoa em vínculo de colaboração/emprego com organização. Inverso: “Tem como colaborador”. Natureza contratual descritiva, sem inferência automática. Sem `other`. |
| `fam.spouse_of` | Familiar | `undirected` | `person` | `person` | `approved` | Vínculo conjugal/união estável entre pessoas. Rótulo simétrico. Sujeito a natureza/confirmação explícita. Restrito a entidades semanticamente compatíveis (pessoas), sem `other`. |
| `fam.parent_of` | Familiar | `directed` | `person` | `person` | `approved` | Relação parental/responsabilidade entre pessoas (`from`→`to`). Inverso: “Filho(a)/dependente de”. Sem `other`. |
| `fam.sibling_of` | Familiar | `undirected` | `person` | `person` | `approved` | Relação de irmandade entre pessoas. Rótulo simétrico. Sem `other`. |
| `fam.relative_of` | Familiar | `undirected` | `person` | `person` | `approved` | Parentesco entre pessoas não especificado pelos tipos anteriores. Grau específico deve ser informado em `description`/`attributes_json` quando relevante. Sem `other`. |
| `biz.supplier_to` | Empresarial | `directed` | `person`, `company`, `economic_group`, `institution` | `person`, `company`, `economic_group`, `institution` | `approved` | Fornecedor de bens/serviços. **Par inverso equivalente:** `biz.customer_of` (mesmo vínculo, sem dois registros). Inverso: “É cliente de (no contexto deste fornecimento)”. Sem `other`. |
| `biz.customer_of` | Empresarial | `directed` | `person`, `company`, `economic_group`, `institution` | `person`, `company`, `economic_group`, `institution` | `approved` | Cliente/contratante. **Par inverso equivalente:** `biz.supplier_to`. Inverso: “É fornecedor de (no contexto deste fornecimento)”. Sem `other`. |
| `biz.contractor_of` | Empresarial | `directed` | `person`, `company`, `economic_group`, `institution` | `person`, `company`, `economic_group`, `institution` | `approved` | Prestador/contratado de. Inverso: “Contrata”. Escolher tipo mais preciso, sem inferência. Sem `other`. |
| `biz.commercial_partner_of` | Empresarial | `undirected` | `person`, `company`, `economic_group`, `institution` | `person`, `company`, `economic_group`, `institution` | `approved` | Parceria comercial simétrica, sem pressupor fornecimento unilateral nem participação societária. Sem `other`. |
| `inst.member_of` | Institucional | `directed` | `person`, `company`, `economic_group`, `institution` | `institution`, `company`, `economic_group` | `approved` | Membro de instituição/organização/rede representada como entidade D1. Inverso: “Tem como membro”. Sem `other`. |
| `inst.regulated_by` | Institucional | `directed` | `person`, `company`, `economic_group`, `institution` | `institution` | `approved` | Sujeição à regulação/supervisão por entidade reguladora/supervisora (tipicamente representada como `institution` em D1) no escopo registrado. Inverso: “Regula”. Sem inferência automática. Sem `other`. |
| `inst.representative_of` | Institucional | `directed` | `person`, `company`, `institution` | `person`, `company`, `economic_group`, `institution` | `approved` | Representação/mandato. Inverso: “Representado por”. Base explicitável quando relevante. Sem `other`. |
| `inst.partner_of` | Institucional | `undirected` | `person`, `company`, `economic_group`, `institution` | `person`, `company`, `economic_group`, `institution` | `approved` | Parceria institucional simétrica. Distinguir de parceria comercial quando aplicável. Sem `other`. |
| `asset.owner_of` | Patrimonial | `directed` | `person`, `company`, `economic_group`, `institution` | — (não aplicável no MVP) | `blocked_by_model` | **Não habilitado no MVP.** Exige extremo “ativo” validável; D1/Foundation não possui tipo de entidade dedicado a ativo. Nenhuma entidade pode ser tratada arbitrariamente como ativo. Distinto de participação societária. Evolução futura de modelo; sem módulo de ativos. Sem `other`. |
| `asset.trustee_of` | Patrimonial | `directed` | `person`, `company`, `institution` | `company`, `economic_group`, `institution` | `approved` | Pessoa ou entidade atuando como trustee/administrador fiduciário de **estrutura/veículo representado como entidade D1** (`company`, `economic_group`, `institution`). Inverso: “Tem como trustee”. Especificidade para não confundir estruturas fiduciárias, empresas e ativos; não cobre ativos não modelados; sem inferência de beneficiários. Sem `other`. |
| `asset.beneficiary_of` | Patrimonial | `directed` | `person`, `company`, `economic_group`, `institution` | `company`, `economic_group`, `institution` | `approved` | Beneficiário de **estrutura/veículo/patrimônio representado como entidade D1** (`company`, `economic_group`, `institution`). Inverso: “Tem como beneficiário”. Especificidade para não confundir estruturas fiduciárias, empresas e ativos; não cobre ativos genéricos não modelados como entidade; distinguir de `corp.beneficial_owner_of` quando aplicável; sem inferência automática. Sem `other`. |
| `asset.co_owner_of` | Patrimonial | `undirected` | `person`, `company`, `economic_group`, `institution` | `person`, `company`, `economic_group`, `institution` | `blocked_by_model` | **Não habilitado no MVP.** Copropriedade requer identificação/representação adequada de ativo/contexto comum não disponível no modelo atual. Depende de evolução futura. Sem `other`. |

**Resumo do congelamento (contagem única e final):** `approved` = **21**; `requires_review` = **1** (`corp.beneficial_owner_of`); `blocked_by_model` = **3** (`corp.partner_in_vehicle`, `asset.owner_of`, `asset.co_owner_of`); `deferred` = **0**. **Total = 25.** `corp.subsidiary_of` **não faz parte** do catálogo proposto/congelado do MVP.

### 2.4 Governança de pares inversos e equivalência semântica

- **Definição semântica:** equivalência entre tipos inversos existe apenas quando dois `relation_type` representam **o mesmo vínculo semântico sob perspectivas opostas**. Não basta similaridade nominal nem igualdade/semelhança literal de identificadores.
- **Documentação explícita:** cada par inverso equivalente deve ser explicitamente documentado no catálogo com `inverse_type_id` **mútuo e bidirecional** (`A.inverse_type_id = B` e `B.inverse_type_id = A`), mapeamento de papéis/extremos e significado preservado.
- **`inverse_label` vs `inverse_type_id`:** `inverse_label` é rótulo de apresentação da perspectiva inversa do **mesmo** `relation_type` (sem novo registro, sem implicar tipo equivalente). `inverse_type_id` declara **tipo equivalente distinto** representando o mesmo vínculo por outra perspectiva.
- **Par equivalente preservado no MVP:** `biz.supplier_to` ↔ `biz.customer_of`.
  - Equivalência canônica: `X --biz.supplier_to--> Y` ≡ `Y --biz.customer_of--> X` (mesmo vínculo de fornecimento).
- **Normalização de orientação para evitar dois registros do mesmo vínculo:** ao criar/validar, o serviço deve determinar a chave semântica do vínculo considerando o mapeamento de equivalência: (a) se o tipo informado `T` possui `inverse_type_id = T_inv`, o vínculo candidato é comparado tanto na forma direta `(T, from, to)` quanto na forma equivalente inversa `(T_inv, to, from)` contra registros existentes não conflitáveis conforme regras; (b) para simétricos aplica-se canonicidade de extremos; (c) a persistência é **única** sob o tipo/perspectiva explicitamente registrado, mas a detecção de conflito/duplicidade considera ambas as perspectivas equivalentes. Assim, registrar `customer_of` quando já existe o `supplier_to` equivalente (ou vice-versa) resulta em **409 Conflict** (duplicidade semântica), sem criar segundo registro.
- **Tipos apenas semelhantes:** sem equivalência semântica declarada, **não** geram conflito automático e podem coexistir apenas se representarem vínculos/fatos distintos e respeitarem demais regras.
- **Novos pares inversos:** exigem revisão humana antes de entrar na taxonomia operacional, com definição semântica clara e regra de compatibilidade. `corp.subsidiary_of` **não** é adicionado no MVP.
- **Conflitos históricos:** identificados e apresentados para revisão humana; **nenhuma fusão ou correção automática** de registros será permitida.

### 2.5 Direcionalidade fixa por tipo (exemplos normativos)

| `relation_type` | Direcionalidade fixa | Observação |
|---|---|---|
| `corp.shareholder_of` | `directed` | Tipo define papéis/extremos; usuário não escolhe direção livremente. |
| `corp.parent_company_of` | `directed` | `from` = controladora, `to` = controlada. |
| `exec.director_of` | `directed` | `from` = pessoa (diretor), `to` = organização. |
| `fam.spouse_of` | `undirected` | Par canônico único entre pessoas. |
| `fam.sibling_of` | `undirected` | Par canônico único entre pessoas. |
| `biz.commercial_partner_of` | `undirected` | Parceria comercial simétrica. |

---

## 3. Direcionalidade e canonicidade

### 3.1 Valores admitidos e determinação pela taxonomia
- **MVP:** apenas `directed` e `undirected`. **`bidirectional` não implementado.**
- **Direcionalidade fixa por tipo:** definida nos metadados da taxonomia (§2). O usuário seleciona o `relation_type` (e, para dirigidas, a atribuição semântica correta dos extremos conforme papéis), **não** escolhe a direção livremente.
- **Validação:** `directionality` informada deve ser idêntica à da taxonomia; se omitida, derivada da taxonomia. Incompatibilidade `relation_type` ↔ `directionality` → **422**.
- **Semântica:** `directed` = `from_entity_id` → `to_entity_id` conforme papéis; `undirected` = vínculo simétrico sem papel distinto por extremo.

### 3.2 Representação canônica de relações simétricas
- **Registro único** por relação simétrica.
- **Ordem canônica:** `from_entity_id = min(id_A, id_B)` e `to_entity_id = max(id_A, id_B)` por comparação lexicográfica determinística dos UUIDs (strings).
- Persistir `directionality = 'undirected'` (consistente com a taxonomia).
- Entradas em ordem invertida (`B, A`) devem ser **normalizadas deterministicamente** para a forma canônica antes da validação de duplicidade/temporalidade; não se cria segundo registro.

### 3.3 Relações dirigidas
- `from`/`to` devem respeitar papéis do tipo e **tipos de entidade permitidos** pela taxonomia; contrato de criação/edição exige definição inequívoca para evitar inversão acidental (422 se inconsistente com papéis/tipos permitidos quando determinável).
- Um único registro representa o vínculo dirigido; inversão de perspectiva é **apresentacional**.

### 3.4 Exibição de inversas e perspectivas equivalentes (sem duplicação)
- **`directed`:** visão em `from` usa rótulo/papel direto; visão em `to` usa rótulo/papel **inverso** (`inverse_label`) derivado da taxonomia — calculado em consulta/apresentação, sem segundo registro.
- **`undirected`:** mesmo registro exibido em ambos os extremos com rótulo simétrico e contraparte relativa à âncora.
- **Pares `inverse_type_id` (equivalentes):** vínculo armazenado **uma única vez**; perspectiva oposta apresentada por mapeamento/rótulo taxonômico derivado quando aplicável, sem criar registro do tipo inverso.
- API deve retornar metadados suficientes (extremos, `directionality`, `relation_type`, rótulos/papéis direto/inverso/simétrico, `inverse_type_id` quando houver, contraparte relativa à âncora).

### 3.5 Exemplos normativos
- **Dirigida (taxonomia fixa):** `corp.shareholder_of` (X→Y). Em X: “Acionista de Empresa Y”; em Y: “Tem como acionista Empresa X”. `directionality=undirected` para este tipo → **422**.
- **Dirigida sem tipo inverso no MVP:** `corp.parent_company_of` (H→O). Em O: “Controlada por Holding H”, sem criar `corp.subsidiary_of`/registro duplicado.
- **Simétrica canônica:** `fam.spouse_of`, par `(min(A,B), max(A,B))` único; entrada invertida normalizada; duplicata semântica → **409**.
- **Par inverso equivalente:** existente `A --biz.supplier_to--> B`; tentativa de `B --biz.customer_of--> A` para o **mesmo vínculo/semântica** → **409 Conflict** (duplicidade semântica por equivalência), sem segundo registro.

---

## 4. Regras de equivalência e duplicidade

### 4.1 Definição e princípios
Duplicata semântica é o registro (ou tentativa) de um **mesmo vínculo** já representado, considerando **semântica do tipo, direção/canonicidade, normalização dos extremos, equivalência de tipos inversos, estado e vigência** das relações existentes — **não apenas igualdade literal de `relation_type`**.

- **Validação determinística e transacional:** executada no serviço, em transação, com suporte de índices (§1.5). A aplicação é autoridade da regra (limites de unicidade complexa/condicional no SQLite).
- **Concorrência:** a validação transacional e as verificações determinísticas devem impedir que duas requisições concorrentes criem duplicidades semânticas (comparação consistente do conjunto relevante antes de persistir; sem criação dupla do mesmo vínculo/intervalo conflitante).
- **Resposta para duplicidade/conflito semântico:** **HTTP 409 Conflict** (ver §8.4).

### 4.2 Conjunto de relações consideradas
- Para fins de conflito/duplicidade operacional, consideram-se relações existentes com `status` em {`active`, `needs_review`, `inactive`} (histórico operacional relevante).
- Relações `archived` **não** bloqueiam, por si só, a criação de um novo registro futuro do mesmo vínculo/novo período (histórico preservado), desde que respeitadas as demais regras (novo registro, sem reativação do arquivado).

### 4.3 Normalização e chave semântica do vínculo
1. **Tipo operacional:** deve ser `approved` (§2). Determinar metadados (direcionalidade, equivalência `inverse_type_id`).
2. **Extremos canônicos:**
   - `undirected`: par canônico `(E1,E2) = (min(id_A,id_B), max(id_A,id_B))`.
   - `directed`: par ordenado `(from,to)` conforme papéis; se existir tipo equivalente `T_inv`, a **forma equivalente inversa** para comparação é `(T_inv, to, from)`.
3. **Comparação:** duplicidade/conflito é avaliado contra a chave semântica normalizada (incluindo forma equivalente inversa quando aplicável), não contra string literal isolada.

### 4.4 Duplicidade semântica e conflitos (regras determinísticas)

1. **Mesma relação dirigida (literal), mesmo vínculo/intervalo conflitante:** conflito/duplicata se existir relação considerada com mesmo `relation_type`, `directionality='directed'`, mesmos `(from,to)` normalizados e vigência equivalente ou sobreposta de forma incompatível (§4.5). → **409**.
2. **Mesma relação simétrica (canônica):** conflito/duplicata se existir relação considerada com mesmo `relation_type`, `directionality='undirected'` e mesmo par canônico, independentemente da ordem de entrada, com vigência equivalente ou sobreposta de forma incompatível (§4.5). → **409**.
3. **Equivalência inversa (mesmo vínculo semântico):** se `T.inverse_type_id = T_inv`, então `A --T--> B` é semanticamente idêntico a `B --T_inv--> A`. É duplicata/conflito criar um quando o equivalente já existe (na forma direta ou inversa) com vigência equivalente ou sobreposta de forma incompatível. → **409**.
4. **Tipos apenas semelhantes (não equivalentes):** sem `inverse_type_id`/equivalência semântica declarada, não há conflito automático; podem coexistir apenas se representarem vínculos/fatos distintos e respeitarem demais regras.
5. **Relação realmente inversa (mesmo tipo, apresentação):** inversão de perspectiva do mesmo registro é apresentação (§3.4), nunca novo registro.

### 4.5 Vigências múltiplas e distinção de nova vigência vs duplicação

**Objetivo:** permitir histórico real do mesmo vínculo semântico em momentos distintos, sem duplicar períodos nem criar inconsistências.

- **Coexistência permitida (mesmo vínculo semântico, mesmo `relation_type` ou par equivalente):** múltiplos registros podem coexistir quando representam **períodos históricos efetivamente diferentes** (intervalos de vigência **distintos e não equivalentes**), preservando histórico de relações encerradas. Exemplo normativo: “João foi diretor da Empresa A entre 2018 e 2020” e “João voltou a ser diretor da Empresa A entre 2023 e 2025” ⇒ registros distintos coexistentes.
- **Períodos equivalentes:** considerados duplicidade do mesmo registro de vigência para o mesmo vínculo semântico. → **409 Conflict**.
- **Lacunas temporais:** **não presumir continuidade**. Um novo período separado por lacuna é um novo registro de vigência (se distinto/não conflitante), não extensão automática do anterior.
- **Sobreposições de vigência (mesmo vínculo semântico):**
  - **Por padrão, rejeitadas como conflito (409)** quando configuram sobreposição/duplicação incompatível ou ambígua (risco de inconsistência).
  - **Exceção (caso a caso, explícito):** sobreposições só podem ser admitidas quando **não** constituírem duplicação equivalente e houver **justificativa semântica documentada** que demonstre coexistência legítima/distinta e explicitamente registrada (ex.: em `justification`, com contexto rastreável). Trata-se de decisão humana explícita registrada; o serviço não infere legitimidade automaticamente.
  - **Regra operacional determinística do MVP:** o serviço deve rejeitar (409) períodos equivalentes e sobreposições; a admissão de qualquer sobreposição excepcional, quando prevista por política explícita, exige justificativa semântica documentada e tratamento explícito/rastreável, **sem correção automática**. Dada a ambiguidade potencial, a política recomendada e segura do MVP é **não admitir sobreposições para o mesmo vínculo semântico** (resolver por ajuste explícito de vigência/novo período distinto) — qualquer exceção operacional deve ser explicitamente justificada e tratada como decisão humana registrada.
- **Relações simultâneas legítimas vs duplicadas:** simultaneidade do **mesmo vínculo semântico e mesmo escopo** é, em geral, duplicação; só se distingue como legítima quando semanticamente distinta e explicitamente justificada (sem inferência). Vínculos de tipos/semânticas diferentes não são o “mesmo vínculo”.
- **Sem correção automática:** o sistema **não** cria novos registros para corrigir períodos anteriores, **não** ajusta vigências automaticamente e **não** presume encerramento/continuidade.
- **Como o serviço distingue nova vigência de tentativa de duplicação (determinístico):**
  1. Normaliza chave semântica do vínculo (§4.3).
  2. Seleciona registros considerados (`active|needs_review|inactive`) da mesma chave semântica.
  3. Compara intervalos de vigência: **equivalente** → duplicata (409); **sobreposto** → conflito (409, salvo exceção explícita documentada e tratada conforme política acima); **disjunto/não sobreposto e não equivalente** → nova vigência permitida (novo registro), preservando histórico.
  4. Campos temporais ausentes devem ser tratados de forma conservadora e determinística (ausência ≠ permissão para inferir não-sobreposição); quando a comparabilidade temporal não puder ser estabelecida com segurança para o mesmo vínculo, tratar como conflito a resolver explicitamente (409) em vez de criar duplicidade ambígua.

### 4.6 Tipos inversos futuros e relações históricas
- Novos tipos inversos/equivalentes só entram com definição semântica explícita, metadados mútuos e revisão humana; antes de uso operacional, avaliar impacto sobre existentes.
- Conflitos/duplicidades semânticas em históricos decorrentes de evolução taxonômica **não** são mesclados/corrigidos automaticamente; devem ser apresentados para revisão humana e tratados explicitamente com rastreabilidade.

### 4.7 Exibição sem duplicação
- Rótulos inversos e mapeamentos de perspectiva/equivalência são resolvidos pela taxonomia em consulta/apresentação. **Nunca** criar segundo registro para representar perspectiva inversa do mesmo vínculo.

---

## 5. Epistemologia e estados

### 5.1 Natureza (dimensão separada)

Vocabulário obrigatório D4: `declarado` | `observado` | `inferido` | `a_confirmar`.

| Valor | Significado operacional | Promoção automática? |
|---|---|---|
| `declarado` | Relação declarada/reportada por fonte/ator. | **Não.** |
| `observado` | Relação observada/constatada com lastro explícito registrado. | **Não** (observação ≠ verificação formal automática). |
| `inferido` | Relação inferida/interpretada a partir de indícios; **não é fato estabelecido**. | **Nunca automaticamente.** |
| `a_confirmar` | Relação pendente de confirmação/triagem. | **Não.** |

Alinhamento: `inferido` coerente com proveniência/claims (distinto de `interpretado` em interações D3).

### 5.2 Verificação (dimensão separada)

Vocabulário operacional D4: `nao_verificado` | `verificado` | `contestado`.

| Valor | Significado |
|---|---|
| `nao_verificado` | Não verificado (padrão). |
| `verificado` | Verificado por ação/critério **explícito** humano e rastreável, com lastro compatível. |
| `contestado` | Contestação registrada; requer tratamento explícito. |

Valores globais `em_verificacao`/`invalido` não são estados primários de conexões D4; registros legados fora do subconjunto tratados defensivamente em leitura/UI sem quebra.

### 5.3 Estado do registro (dimensão separada)

Vocabulário obrigatório D4: `active` | `needs_review` | `inactive` | `archived`.

| Valor | Semântica |
|---|---|
| `active` | Vigente para uso operacional corrente (sujeita à natureza/verificação). |
| `needs_review` | Requer revisão humana (dúvida, conflito, pendência, contestação em análise). |
| `inactive` | Cessada/não vigente operacionalmente, mantida para histórico. |
| `archived` | Retirada do uso ativo com retenção histórica/auditável; fora de listagens ativas por padrão. **Não reativada diretamente no MVP** (§1.7). |

`status` ≠ `verification_status` ≠ `nature`.

### 5.4 Regras anti-promoção e transições

1. **Proibição absoluta de automação:** o sistema **nunca** cria, confirma, verifica ou promove relações automaticamente a partir de D2, D3, claims, evidências, interações, padrões, inferências ou estruturas societárias presumidas.
2. **`nature = inferido` não é fato** e nunca é apresentado/contabilizado como fato verificado.
3. **Bloqueio de verificação direta de inferência:** rejeitar (**422**) qualquer tentativa de `verification_status = verificado` enquanto `nature = inferido`. Promoção exige reclassificação explícita de `nature` para `declarado`/`observado` (com lastro/justificativa) **e** ação explícita de verificação, em passos rastreáveis.
4. **Sem upgrade implícito:** anexar vínculos probatórios/localizador/campos **não** altera `nature` nem `verification_status`.
5. **Transições explícitas e auditadas:** mudanças de campos sensíveis apenas por ação explícita, com `audit_events` e `data_changes` (before/after, motivo/justificativa quando aplicável).
6. **Contestação/revisão:** explícitas; nunca resolvidas automaticamente.

**Matriz normativa de transições:**

| Transição | Permitido | Condições |
|---|---|---|
| `nature: inferido` → `verification_status: verificado` (mantendo `inferido`) | **Não** | Proibido (422). |
| `nature: inferido` → `nature: declarado|observado` | Sim (explícito) | Ação humana explícita, justificativa recomendada/registrável, rastreável. |
| `nature: declarado|observado|a_confirmar` → `verification_status: verificado` | Sim (explícito) | Ação explícita com lastro/justificativa; nunca automático. |
| `verification_status: nao_verificado` → `contestado` | Sim (explícito) | Justificativa recomendada/registrável. |
| `status: active|needs_review|inactive` → `archived` | Sim (explícito) | Arquivamento rastreável. |
| `status: archived` → `active|needs_review|inactive` | **Não (MVP)** | Reativação direta proibida; criar novo registro se vínculo se restabelecer (§1.7). |
| Qualquer alteração por job/inferência/automação | **Não** | — |

### 5.5 Confiança (`confidence`)
- **Opcional/nullable; nunca obrigatória.** Se informada: `[0.0, 1.0]` (422 fora da faixa). Não é proxy de verdade, não substitui natureza/verificação e não dispara transição automática. Sem fundamento ⇒ `NULL`.

---

## 6. Semântica temporal

### 6.1 Campos preservados e significados

| Campo | Significado |
|---|---|
| `occurred_at` | Momento de **acontecimento específico** relacionado à relação (evento pontual). Não equivale, por si só, à vigência completa. |
| `valid_from` | Início da **validade/vigência** da relação, quando conhecido. |
| `valid_to` | Término da **validade/vigência** da relação, quando conhecido. |
| `time_precision` | **Precisão temporal disponível** (granularidade/certeza declarada) conforme vocabulário controlado. |

**Modelo mantido no MVP:** `occurred_at`, `valid_from`, `valid_to`, `time_precision` preservados sem introdução de novas estruturas e sem alteração silenciosa dos campos existentes.

### 6.2 Vocabulário controlado de `time_precision` (D4)

Valores permitidos: `exact` | `month` | `year` | `estimated` | `unknown`.

| Valor | Significado |
|---|---|
| `exact` | Data/hora conhecida com precisão exata conforme fonte/registro. |
| `month` | Precisão em mês/ano (dia/hora exatos desconhecidos ou não aplicáveis). |
| `year` | Precisão em ano (mês/dia exatos desconhecidos ou não aplicáveis). |
| `estimated` | Data aproximada/estimada explicitamente como tal. |
| `unknown` | Precisão temporal desconhecida/não informada. |

> D4 adota este vocabulário para `relationships`. **D3 (`entity_interactions.time_precision`) permanece inalterado.**

### 6.3 Acontecimento vs período de validade
- `occurred_at` = evento/instante associado; `valid_from`/`valid_to` = intervalo de vigência. Podem coexistir.
- Não inferir vigência a partir de `occurred_at` nem evento a partir de vigência.
- Campos podem ser `NULL` quando a informação correspondente não é conhecida.

### 6.4 Regras obrigatórias (sem invenção de precisão)
- **Datas parciais não podem ser convertidas em datas exatas fictícias.** Registrar a melhor representação possível sem fabricar componentes ausentes e declarar `time_precision` coerente (`month`, `year`) quando aplicável.
- **Informações aproximadas devem ser identificadas como `estimated`** (não como exatas).
- **Datas desconhecidas permanecem desconhecidas** (`NULL` nos campos aplicáveis; `time_precision = unknown` ou valor coerente com o que se sabe). Relação com existência conhecida mas data inicial exata desconhecida: `valid_from` (e/ou demais campos) pode permanecer `NULL`, com limitação explicitada em `description`/`justification`.
- **A precisão informada deve ser compatível com a evidência disponível.** É vedado declarar precisão maior que a efetivamente conhecida/registrada.
- Incertezas/nuances devem ser explicitadas em `description`/`justification` quando necessário.

### 6.5 Validações de coerência temporal (determinísticas)
- `valid_to >= valid_from` quando ambos informados (422 caso contrário).
- `time_precision` no vocabulário controlado (422 se inválido) e coerente com a informação declarada.
- Campos temporais independentes na persistência, interpretados conforme semântica acima (sem inferência automática).
- Comparação de vigências para duplicidade/conflito segue §4.5 (tratamento conservador quando comparabilidade não for determinável com segurança).

### 6.6 Limitação do modelo atual e evolução futura (registrada)
- **Limitação:** o uso de campos `DateTime(tz)` com **uma única precisão temporal** (`time_precision`) **não expressa perfeitamente** (a) granularidades parciais distintas por campo (ex.: `valid_from` apenas por ano e `occurred_at` exato) e (b) datas parciais nativas (ano/mês) sem convenção inventada.
- **Mitigação no MVP:** não inventar componentes de data/precisão; declarar precisão compatível; detalhar nuances textualmente; aplicar regras de comparação conservadoras.
- **Evolução futura (não implementada):** possibilidade de **granularidade temporal individual por campo** e/ou representação de data parcial tipada, a ser avaliada em evolução controlada **sem alterar silenciosamente** o modelo/contrato atual.

---

## 7. Proveniência e autoria

### 7.1 Proveniência (reuso, sem duplicação)
- Proveniência e rastreabilidade obrigatórias e explícitas. D4 **reutiliza** `claim_id`, `evidence_id`, `audit_events`, `data_changes`, `processing_events` (quando aplicável), sem duplicar conteúdo probatório.
- **`claim_id` / `evidence_id` (opcionais):** vínculos a artefatos D2. Se ambos informados, coerência claim↔evidence deve ser validada (422 em inconsistência). Referências inexistentes → 404.
- **`source_locator` (opcional):** localizador textual direto complementar; **não substitui** evidência formal nem recria cadeia D2.
- **Evitado:** FKs diretas redundantes e cópia de `snippet`/`excerpt`/conteúdo (§1.4).
- **Regras:** nenhuma criação automática de relações a partir de Claims, Evidences ou Interactions; vínculos informados explicitamente. Conteúdo externo tratado como dado não confiável.

### 7.2 Autoria (`created_by`) — formato controlado e compatibilidade

**Formato controlado canônico:** `<actor_type>:<actor_id>`

| Tipo de ator | Identificador | Significado |
|---|---|---|
| Usuário humano | `human_user` | Cadastro realizado por usuário humano. |
| Agente de IA | `ai_agent` | Cadastro realizado por agente de IA (identificado). |
| Processo interno | `internal_process` | Cadastro realizado por processo interno do sistema. |

**Regras normativas:**
- `<actor_type>` ∈ {`human_user`, `ai_agent`, `internal_process`}.
- `<actor_id>`: identificador estável e controlado do ator (sem espaços; formato determinístico recomendado `[A-Za-z0-9._-]{1,80}`), compatível com `String(100)`.
- **Regex normativa (contrato):** `^(human_user|ai_agent|internal_process):[A-Za-z0-9._-]{1,80}$`.
- **Novos registros D4:** **exigem autoria identificada** em formato controlado (422 se ausente/inválido na criação D4).
- **`NULL`:** aceito **somente** para **registros legados** ou **situações de compatibilidade explicitamente justificadas**; não admitido como padrão para novas criações D4. Leitura/serialização deve ser **defensiva** para legados fora do formato.
- **Agentes futuros:** devem possuir identificadores próprios (`ai_agent:<id>` estável). **Nenhum agente poderá criar relações automaticamente durante a implementação de D4.**
- **Sem sistema dedicado de identidade:** solução mais simples compatível com a arquitetura atual (campo string existente), sem criar tabelas/estruturas de usuários ou identidade de agentes para esta finalidade.
- **Distinção e rastreabilidade:** `created_by` identifica a autoria de criação e **não substitui** `audit_events` nem `data_changes`. Alterações posteriores (inclusive por outros atores) devem permanecer rastreáveis em `audit_events` e `data_changes` (before/after, contexto). A autoria de criação deve ser preservada.

---

## 8. Contratos de API

### 8.1 Base e princípios
- **Base:** `/api/v1/dossiers` (consistente com D1–D3). Schemas Pydantic dedicados, serviço `knowledge/dossiers/connections_service.py`, endpoints sob `dossiers`/`connections`.
- Operações explícitas, determinísticas, rastreáveis, transacionais quando aplicável. Sem inferência, sem promoção automática, sem criação automática a partir de D2/D3.
- Conteúdo tratado como dado não confiável (validação/serialização segura).
- **Aplicação efetiva das restrições de taxonomia:** a API e o serviço devem aplicar efetivamente as restrições definidas pela taxonomia congelada — incluindo `relation_type` operacional aprovado, direcionalidade fixa, e **tipos de entidade permitidos na origem e no destino** (compatibilidade semântica, com vedação de `other` quando não justificado/documentado no tipo) — rejeitando com 422 qualquer incompatibilidade.

### 8.2 Endpoints (proposta)

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/entities/{entity_id}/connections` | Cria relação da entidade âncora. Valida tipo operacional aprovado, direcionalidade fixa, tipos de entidade permitidos (origem/destino), extremos/papéis, canonicidade/equivalência inversa, **duplicidade semântica e vigências** (409), integridade, temporalidade, epistemologia, autoria obrigatória D4 e rastreabilidade. |
| `GET` | `/entities/{entity_id}/connections` | Lista conexões (incoming/outgoing/ambas, incluindo simétricas). Filtros: `direction`, `relation_type`, `category`, `nature`, `verification_status`, `status`, `occurred_from/to`, `valid_from/to`, `has_evidence`, `q`, `sort`, `limit`, `offset`. |
| `GET` | `/connections/{connection_id}` | Detalhe com metadados taxonômicos (rótulos/papéis direto/inverso/simétrico, equivalência), extremos, proveniência e metadados. |
| `PATCH` | `/connections/{connection_id}` | Atualização parcial **explícita** (campos permitidos, transições de `nature`/`verification_status`/`status`, vínculos, temporalidade, metadados). Revalida regras (incluindo anti-promoção, duplicidade/vigência quando aplicável, integridade/coerência, compatibilidade semântica de tipos). **Arquivado não é reativado** (422 se tentativa). Registra `audit_events`/`data_changes`. |
| `GET` | `/entities/{entity_id}/connections/summary` | Resumo determinístico (contagens por natureza, verificação, estado, tipo/categoria, perspectiva, indicadores de lastro). |

> **Sem endpoint de delete físico no MVP.** Ciclo de vida via `status`.

### 8.3 Contratos de request/response (conceitual)

**Create (POST):**
- Obrigatórios: contraparte (ex.: `other_entity_id`), `relation_type` (ID estável **aprovado**), `created_by` (formato controlado, obrigatório para novo registro D4).
- Perspectiva dirigida: definição explícita e inequívoca de `from`/`to` conforme papéis do tipo (evitar inversão semântica).
- Opcionais: `description`, `justification`, `nature`, `verification_status`, `status` (conforme regras), `occurred_at`, `valid_from`, `valid_to`, `time_precision`, `source_locator`, `claim_id`, `evidence_id`, `confidence`.
- `directionality`: não é escolha livre; se enviada, deve coincidir com a taxonomia (422 se divergente), senão derivada.
- **Validação de compatibilidade semântica:** os `entity_type` das entidades envolvidas devem pertencer aos conjuntos permitidos (origem/destino) do `relation_type` selecionado, conforme taxonomia congelada (422 em incompatibilidade).

**Update (PATCH):**
- Atualização parcial explícita. Mudança de tipo/extremos (se permitida) exige revalidação completa (taxonomia aprovada, direcionalidade, tipos de entidade permitidos, canonicidade/equivalência, duplicidade/vigência). Transições sujeitas a §5.4. Tentativa de reativar `archived` → **422**. Sem correções automáticas de períodos.

**Response:** campos persistidos + resumos de entidades (`id`, nome, `entity_type`), `category`, `directionality`, rótulos/papéis direto/inverso/simétrico, `inverse_type_id` (se aplicável), perspectiva/contraparte relativa à âncora, indicadores de lastro, timestamps. Rótulos derivados deterministicamente da taxonomia.

### 8.4 Erros e contratos (normativo)

| Código | Significado | Exemplos (não exaustivos) |
|---|---|---|
| **409 Conflict** | **Conflito com relação existente ou duplicidade semântica** (determinística e transacional) | (a) criar relação dirigida idêntica (mesmo tipo e extremos normalizados) com período equivalente/sobreposto conflitante; (b) criar simétrica A–B quando já existe B–A/canônica equivalente para o mesmo vínculo/período conflitante; (c) criar `B --biz.customer_of--> A` quando já existe `A --biz.supplier_to--> B` equivalente (ou vice-versa) para o mesmo vínculo/período conflitante; (d) tentativa de novo registro que conflita com vigência existente do mesmo vínculo semântico (equivalente/sobreposição incompatível) sem resolução explícita permitida; (e) colisão concorrente detectada que resultaria em duplicidade semântica. |
| **422 Unprocessable Entity** | **Dados inválidos, combinação incompatível de campos ou violação de regras de validação** | `relation_type` inexistente/não aprovado; incompatibilidade `relation_type`↔`directionality`; **tipos de entidade origem/destino não permitidos pela taxonomia (incompatibilidade semântica, inclusive uso de `other` quando vedado)**; vocabulário inválido (`nature`, `verification_status`, `status`, `time_precision`); auto-relação; `confidence` fora de `[0,1]`; `valid_to < valid_from`; `created_by` ausente/inválido em novo registro D4; tentativa de `inferido`→`verificado` mantendo `inferido`; tentativa de reativar `archived` via `PATCH`; incoerência claim↔evidence; extremos inconsistentes com papéis; campos temporais/precisão inválidos ou violação de regras de não invenção quando determinável. |
| **404 Not Found** | **Entidade ou referência inexistente** | `entity_id` (âncora/contraparte) inexistente; `connection_id` inexistente; `claim_id` ou `evidence_id` referenciado inexistente. |

**Contrato de erro (conceitual):** resposta JSON com código de erro estável, mensagem clara e orientada à correção, e, quando aplicável, identificação do campo/regra violada e/ou do conflito detectado, **sem expor detalhes internos sensíveis**. O padrão deve ser consistente em toda a API D4.

### 8.5 Rastreabilidade
- Criação/atualização: `audit_events` (ação específica de conexão) e `data_changes` (`entity_table='relationships'`, before/after, ator/motivo quando aplicável). `processing_events` não utilizado por padrão.

---

## 9. Requisitos de interface

### 9.1 Princípios
- Seção **Relações** em `DossierEntityPage` (substituir placeholder D4), componente dedicado (ex.: `ConnectionsWorkspace`), alinhado a D2/D3.
- **Dados exclusivamente reais cadastrados.** Sem simulação, sem relações inferidas, sem arestas/contagens geradas por heurística.
- Estados claros: loading, erro (com retry), vazio, sucesso; feedback explícito.

### 9.2 Funcionalidades planejadas (MVP)
1. **Lista estruturada (principal):** conexões com contraparte (nome/tipo/link), tipo/rótulo por perspectiva, direção/papéis, natureza, verificação, estado, vigência/`occurred_at` e `time_precision`, indicadores de lastro, atualização.
2. **Filtros e pesquisa:** direção/perspectiva, `relation_type` (apenas aprovados), categoria, natureza, verificação, estado, período/vigência, presença de evidência/claim, busca textual `q`, ordenação.
3. **Detalhe da relação:** extremos, tipo/rótulos (direto/inverso/simétrico), papéis, `directionality`, natureza, verificação, estado, temporalidade/precisão, descrição, justificativa, `source_locator`, vínculos `claim_id`/`evidence_id`, `confidence` (se houver), `created_by` (interpretação controlada/defensiva para legado), timestamps. Distinção visual clara de `inferido`/`a_confirmar` e de não verificado/contestado; **nunca** apresentar inferido como fato verificado.
4. **Navegação:** acesso ao dossiê das entidades relacionadas.
5. **Criação e edição explícita:** seleção de contraparte e `relation_type` a partir da **taxonomia aprovada** (sem texto livre). Direcionalidade derivada/fixa pelo tipo (UI orienta papéis/origem-destino). A UI deve restringir/apresentar opções de contraparte e papéis de forma coerente com os **tipos de entidade permitidos** pelo tipo selecionado, alinhada às validações do servidor. Campos temporais com `time_precision` controlado, natureza/estado/verificação, proveniência, `confidence` opcional, `created_by` conforme contrato, descrição/justificativa. Ações explícitas de estado/verificação (revisão, contestar, arquivar, verificar quando permitido) com confirmações e justificativa quando aplicável. Sem reativação direta de arquivados (oferecer criação de novo registro quando aplicável).
6. **Resumo determinístico:** contagens/distribuições conforme API, sem scores inferidos.
7. **Grafo simples complementar (planejado, condicionado à viabilidade técnica):**
   - Reutilizar **Cytoscape.js** já presente no projeto (sem dependências novas).
   - Exibir **somente relações reais cadastradas**.
   - Limitar a visualização a **ego-network de 1 salto** na primeira versão.
   - Diferenciar visualmente relações **dirigidas** e **simétricas**.
   - Permitir navegação entre entidades.
   - Exibir rótulos derivados da taxonomia.
   - **Não** apresentar inferências como relações confirmadas; **não** implementar simulações ou previsões.
   - **A lista estruturada continua sendo a interface principal.** O grafo **não pode bloquear a entrega do MVP**.
   - **Fallback obrigatório:** se a implementação apresentar complexidade/instabilidade desproporcional, entregar **lista + filtros + detalhe + navegação entre entidades**.

### 9.3 Contratos e reuso de UI
- Extensões previstas: `ConnectionsWorkspace` e componentes de lista/filtro/detalhe/formulário/grafo (opcional), utilitários taxonômicos/temporais, `lib/api/client.ts` e `lib/api/types.ts`. D5 permanece placeholder. Validações de cliente alinhadas ao servidor (sem substituí-lo).

---

## 10. Estratégia de testes

Implementação (quando autorizada) deve garantir cobertura automatizada (pytest, DB temporário) e verificações de qualidade, no mínimo:

1. **Relações dirigidas:** criação/leitura/atualização/listagem por perspectiva, extremos/papéis corretos, rótulos direto/inverso derivados sem duplicação.
2. **Relações simétricas:** persistência canônica `(min,max)` e `undirected`, exibição em ambos os extremos, normalização/bloqueio de ordem invertida.
3. **Direcionalidade determinada pela taxonomia:** rejeição **422** para incompatibilidade `relation_type`↔`directionality` e para tipos não aprovados; derivação consistente.
4. **Duplicidade semântica (409) e concorrência lógica:** bloqueio A–B vs B–A (simétrica), duplicata dirigida idêntica, **duplicata por equivalência inversa** (`biz.supplier_to`/`biz.customer_of`), períodos equivalentes e sobreposições conflitantes do mesmo vínculo semântico; permissão de vigências distintas não sobrepostas; validação determinística transacional que impeça duplicidade por requisições concorrentes.
5. **Vigências múltiplas e histórico:** coexistência de períodos distintos do mesmo vínculo; preservação de registros encerrados/inativos; sem correção automática de períodos; não reativação direta de `archived` (422) e criação de novo registro para vínculo restabelecido.
6. **Relações inversas/perspectivas equivalentes (apresentação):** metadados/rótulos corretos sem segundo registro.
7. **Natureza e verificação:** vocabulários aceitos; proibição de `inferido`+`verificado`; nenhuma promoção/alteração automática; transições explícitas válidas rastreadas.
8. **Integridade de referências e taxonomia:** entidades e referências existentes (404 quando aplicável); **tipos de entidade origem/destino permitidos por tipo efetivamente validados** (422 em incompatibilidade semântica, incluindo rejeição de `other` quando vedado pelo tipo), inclusive em relações familiares, executivas e patrimoniais aprovadas; coerência claim↔evidence (422); `relation_type` inexistente/não aprovado → 422.
9. **Coerência temporal e precisão:** `valid_to >= valid_from`; `time_precision` no vocabulário D4; ausência de invenção de precisão (conforme contrato); combinações válidas de `occurred_at`/vigência/`NULL`.
10. **Autoria (`created_by`):** obrigatório e em formato controlado para novos registros D4 (422 se ausente/inválido); tolerância defensiva de leitura para legados/compatibilidade; preservação de autoria e coexistência com auditoria.
11. **Arquivamento/inativação:** transições válidas, efeitos em filtros/listagens/resumo, preservação histórica, reativação direta de `archived` bloqueada.
12. **Rastreabilidade:** `audit_events` e `data_changes` em criação e mutações relevantes, com before/after consistentes.
13. **Compatibilidade Foundation e D1–D3:** migração aditiva aplicada em DB temporário até head D4; regressão da suíte existente; FKs/cascatas/SET NULL preservados; `relationships` legadas legíveis; sem quebra de fluxos D1–D3.
14. **Qualidade estática/build (quando implementado):** ruff, mypy (backend), typecheck/lint/build (frontend).
15. **UI (quando implementado):** lista/filtros/detalhe/navegação, criação/edição explícita com taxonomia aprovada e compatibilidade semântica de entidades, regras temporais/epistêmicas visíveis, grafo (se habilitado) ou fallback, sem erros de console, persistência e rastreabilidade refletidas.

---

## 11. Critérios de aceitação

- Reuso exclusivo de `relationships` com migração **aditiva** (filha de `b6c7d8e9f0a1`), sem segunda estrutura e sem alterações destrutivas em Foundation/D1–D3.
- Taxonomia operacional **congelada**: apenas tipos `approved` utilizáveis no MVP; direcionalidade fixa por tipo validada (422 em incompatibilidade); tipos não representáveis com entidades D1 não habilitados.
- **Compatibilidade semântica de tipos de entidade aplicada:** para cada `relation_type`, origem/destino restritas conforme taxonomia (relações familiares e executivas compatíveis; patrimoniais aprovados específicos; `other` vedado no MVP sem justificativa documentada), com validação efetiva pela API/serviço (422).
- Canonicidade simétrica (UUID lexicográfico) e normalização de equivalência inversa sem duplicar registros.
- **Duplicidade semântica/conflitos tratados como 409** (determinístico, transacional, incluindo pares equivalentes e conflitos de vigência definidos); **422/404** conforme contrato.
- Vigências múltiplas do mesmo vínculo permitidas apenas para períodos distintos/não conflitantes, com histórico preservado e sem correção automática; **arquivados não reativados diretamente** (novo registro para vínculo restabelecido).
- Natureza, verificação e estado separados; `confidence` opcional; nenhuma promoção automática de `inferido` a verificado/fato; nenhuma criação automática a partir de claims/evidences/interactions/inferências.
- Semântica temporal formalizada com vocabulário controlado, coerência validada e **sem invenção de precisão**; modelo temporal atual preservado (limitação e evolução futura registradas).
- `created_by` obrigatório e controlado para novos registros D4; compatibilidade defensiva para legados; sem criação automática por agentes em D4; autoria distinta de auditoria.
- Proveniência/integridade referencial validadas com reuso D2 sem duplicação redundante.
- Arquivamento/inativação funcionais; sem hard delete em UI/MVP.
- UI: lista estruturada principal, filtros/pesquisa, detalhe, navegação e ações explícitas; grafo Cytoscape.js complementar se viável, caso contrário fallback obrigatório — sempre com dados reais, sem simulação.
- Rastreabilidade completa (`audit_events`, `data_changes`) e compatibilidade Foundation/D1–D3 preservada.

---

## 12. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Unicidade/duplicidade semântica e temporal não totalmente exprimível por constraints no SQLite | Duplicatas ou conflitos inconsistentes | Validação determinística no serviço em transação, normalização canônica/equivalente, comparação conservadora de vigências, índices de suporte, testes (incluindo concorrência lógica). |
| Ambiguidade em sobreposição de vigências para o mesmo vínculo | Inconsistência histórica | Rejeição padrão de sobreposições/equivalências como 409; exigência de resolução explícita; exceções apenas com justificativa semântica documentada e decisão humana rastreável; sem correção automática. |
| Atribuição incorreta de `from`/`to` em tipos dirigidos | Semântica invertida | Contrato/UI orientado por papéis, validação de tipos permitidos por extremo, preview explícito, rótulos derivados corretos. |
| Uso permissivo de `entity_type` genérico (`other`) em relações | Grafo semanticamente inadequado/ruidoso | **Restrição por taxonomia**: `other` vedado no catálogo MVP sem justificativa semântica documentada; validação efetiva em API/serviço (422); testes específicos. |
| Tipos sensíveis/modelo limitado (`corp.partner_in_vehicle`, patrimoniais, UBO) | Representação imprecisa | Catálogo congelado com tipos não representáveis bloqueados/não aprovados; restrições explícitas e específicas; sem inferência automática; `corp.beneficial_owner_of` condicionado a revisão/aprovação operacional. |
| Limitação temporal (precisão única por registro, `DateTime`) | Perda de nuance | Vocabulário controlado, proibição de invenção de precisão, campos textuais, comparação conservadora, evolução futura registrada sem alteração silenciosa. |
| Divergência de vocabulários com D1–D3 (`time_precision`, `nature`, `verification_status`) | Interpretação inconsistente | Vocabulários D4 explícitos, rotulagem/mapeamento claro, leitura defensiva de legados, documentação de diferenças. |
| Evolução de pares inversos e conflitos históricos | Duplicidades retroativas | Governança formal, `inverse_type_id` explícito, sem correção/fusão automática, revisão humana com rastreabilidade. |
| Autoria legada fora do formato controlado | Autoria ambígua em histórico | Exigência de formato para novos D4, tolerância defensiva em leitura, sem reescrita automática de histórico. |
| Grafo com muitas arestas em ambiente local (8 GB RAM) | Lentidão | Ego-rede 1 salto, limites/carregamento sob demanda, layout simples, fallback obrigatório para lista. |
| Regressão em Foundation/D1–D3 ou legados de `relationships` | Quebra funcional | Migração estritamente aditiva, defaults seguros, compatibilidade de leitura, testes de regressão, preservação de FKs/comportamentos. |
| Promoção indevida de inferência | Violação de princípio central | Guardas de serviço, matriz de transições, testes negativos, auditoria obrigatória. |

---

## 13. Limitações do MVP

- **Tipos não operacionais no MVP:** `corp.partner_in_vehicle`, `asset.owner_of`, `asset.co_owner_of` (`blocked_by_model`) e `corp.beneficial_owner_of` (`requires_review`) não são habilitados para novos registros até resolução das condições/dependências indicadas.
- **Representação de veículos/ativos:** sem campo tipado de veículo comum em `corp.partner_in_vehicle` e sem tipo de entidade dedicado a “ativo” em D1; titularidade genérica de ativos e copropriedade de ativos não modelados como entidade não são representáveis corretamente. Tipos patrimoniais aprovados (`asset.trustee_of`, `asset.beneficiary_of`) restringem-se a estruturas/veículos representados como entidades D1 (`company`, `economic_group`, `institution`), sem confundir com ativos.
- **Restrição semântica de `entity_type`:** `other` (tipo existente em D1) não é aceito em nenhum tipo de relação do catálogo congelado do MVP por ausência de justificativa semântica documentada; eventual uso futuro exigirá justificativa e aprovação explícitas no tipo.
- **Temporalidade:** `DateTime(tz)` com `time_precision` único não expressa granularidades distintas por campo nem datas parciais nativas; mitigado por contrato conservador, sem granularidade por campo no MVP.
- **Duplicidade/vigência:** comparação temporal conservadora quando informações são insuficientes (pode exigir resolução explícita); exceções de sobreposição, se admitidas, dependem de justificativa explícita e não de inferência.
- **Arquivamento:** sem reativação direta de registros `archived` no MVP (requer novo registro).
- **Autoria legada:** registros anteriores ao formato controlado podem exigir interpretação defensiva (sem normalização retroativa automática).
- **Grafo:** complementar e condicionado à viabilidade; pode ser omitido em favor do fallback (lista/filtros/detalhe/navegação).
- **Identidade:** sem sistema dedicado de usuários/identidade de agentes; `created_by` usa formato controlado simples compatível.
- **Escopo:** sem D5, sem simulação/previsão, sem inferência/fusão/criação automática, sem serviços externos/dependências pagas.

---

## 14. Decisões futuras e dependências

- **Evolução do modelo de entidades (dependência para tipos bloqueados):** modelagem dedicada/representação validável de ativos (habilitar/reavaliar `asset.owner_of`, `asset.co_owner_of`) e representação adequada de veículo societário comum para coparticipação (`corp.partner_in_vehicle`). Sem criação de novas estruturas nesta etapa.
- **`corp.beneficial_owner_of`:** decisão humana explícita para habilitação operacional (`approved`) após confirmação de critérios de evidência/validação e, se necessário, refinamento adicional de controles.
- **Uso futuro de `other` em relações:** somente mediante justificativa semântica documentada e explícita no tipo, com revisão/aprovação humana (não presumido).
- **Granularidade temporal por campo / datas parciais tipadas:** evolução futura possível sem alteração silenciosa do contrato atual.
- **Governança de pares inversos futuros:** introdução de novos pares (ex.: eventual `corp.subsidiary_of`) somente com justificativa, definição semântica, metadados mútuos, revisão humana e tratamento explícito de históricos conflitantes (sem automação).
- **Políticas operacionais finas:** eventual formalização futura de exceções de sobreposição de vigência (se adotadas além da recomendação conservadora do MVP), e processos controlados para revisão de conflitos históricos detectados.
- **Grafo:** evolução além da ego-network de 1 salto apenas se viável dentro das restrições de desempenho/local-first.

---

**D4 permanece não implementado.** Este planejamento está finalizado para revisão e **aguarda aprovação explícita** antes de qualquer implementação, migração, alteração de banco, criação de código/endpoints/UI, instalação de dependências, commit ou push.