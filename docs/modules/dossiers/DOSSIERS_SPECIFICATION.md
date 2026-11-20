# DOSSIERS — Especificação Funcional e Técnica (V1.0)

> **Módulo:** Dossiers · **Versão:** 1.0 · **Natureza:** inteligência e conhecimento · **Execução:** local-first · **Status:** implementação incremental (D1–D3 implementados, validados e publicados; D4–D6 pendentes, D4 condicionado a planejamento técnico aprovado).

Esta cópia registra a especificação aprovada do módulo Dossiers no repositório para rastreabilidade. A implementação ocorre por subetapas autorizadas, com reuso de Foundation e estruturas existentes, persistência local (SQLite/Alembic), proveniência/rastreabilidade e UI sem simulação.

## 1. Visão e princípio central
O Dossiers organiza, armazena, relaciona e apresenta informações sobre pessoas, empresas, grupos econômicos, holdings, instituições e outras entidades relevantes, transformando informações dispersas em dossiês estruturados, rastreáveis e continuamente atualizáveis.

**Princípio:** o SCOUT preserva contexto, origem, validade e grau de confiança de cada informação. Informação registrada não é automaticamente verdadeira; inferências não são promovidas a fato sem fluxo/ação explícita. Estados epistemológicos e de verificação são explícitos.

## 2. Escopo funcional (V1.0)
1. **Entity Profiles (D1)** — cadastro/consulta/edição/pesquisa/detecção de duplicidades (sem fusão automática), perfis e página individual.
2. **Research & Evidence (D2)** — fontes de pesquisa, documentos/referências, afirmações com classificação epistemológica, evidências e conflitos, com proveniência e rastreabilidade.
3. **Relationship History (D3)** — histórico de interações por entidade em linha do tempo, com natureza explícita (`declarado`, `observado`, `interpretado`, `a_confirmar`), contexto/proveniência e estados rastreáveis.
4. **Connections (D4)** — relações entre entidades, temporalidade, evidências e visualização simplificada (pendente).
5. **Strategic Insights (D5)** — hipóteses/oportunidades com fundamentação e estados, sem execução automática (pendente).

## 3. Requisitos transversais
- Reutilizar Foundation e estruturas existentes (`entities`, `relationships`, claims, evidence, sources, documents, raw_records, `data_changes`, `audit_events`, `processing_events` etc.) sem duplicação.
- Persistência local (SQLite/Alembic), integridade referencial, migrações versionadas e aditivas, proveniência e rastreabilidade.
- UI de consulta/análise (não apenas formulários), pesquisa local, estados claros (loading/erro/vazio/sucesso), sem simulação de dados/funcionalidades.
- Funcionalidades determinísticas primeiro; integração futura com IA local (Ollama) opcional e sob demanda, sem promover inferências a fatos automaticamente.
- Segurança/privacidade local, minimização de dados, tratamento de conteúdo externo como dado não confiável.
- Implementação incremental por subetapas autorizadas, com testes e documentação.

## 4. Estado de implementação
- **D1 — Entity Profiles:** implementado e entregue (`b7d1e2f3a4c5`). CRUD/pesquisa/filtros, normalização, duplicidades sugeridas sem fusão automática, UI home e página da entidade.
- **D2 — Research & Evidence:** implementado e entregue (migrações `c1d2e3f4a5b6` → `a5b6c7d8e9f0`). Fontes de pesquisa, documentos/referências, afirmações, evidências e conflitos com proveniência/rastreabilidade e Research Workspace determinístico/manual-first, sem promoção automática a fato.
- **D3 — Relationship History:** implementado, validado (suíte automatizada, API assistida e smoke test de UI) e **publicado**. Migração aditiva `b6c7d8e9f0a1` (`entity_interactions`, filha de `a5b6c7d8e9f0`), serviço/API/UI/testes e documentação; migração aplicada ao DB local (head `b6c7d8e9f0a1`). D3 é distinto de D2 (interações/timeline vs pesquisa/evidências) e não utiliza/redefine `relationships` (reservado a D4).
- **D4–D6:** pendentes de autorização/implementação (seções Relações/Insights permanecem placeholders sem simulação).

## 5. Restrições preservadas
- Sem fusão automática de entidades, sem promoção automática de inferências a fatos, sem coleta/agentes autônomos ou indiscriminados.
- Sem dependências pagas/comerciais obrigatórias, sem upload remoto dedicado, sem paralelismo pesado.
- Operação local-first (loopback/armazenamento local), controle humano e rastreabilidade (`audit_events`, `data_changes`, `processing_events` quando aplicável).
