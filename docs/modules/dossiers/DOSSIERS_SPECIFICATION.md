# DOSSIERS — Especificação Funcional e Técnica (V1.0)

> **Módulo:** Dossiers · **Versão:** 1.0 · **Natureza:** inteligência e conhecimento · **Execução:** local-first · **Status:** especificação aprovada para implementação incremental (D1–D6).

Esta cópia registra a especificação aprovada do módulo Dossiers no repositório para rastreabilidade. A implementação ocorre por subetapas autorizadas. O conteúdo normativo completo foi fornecido e aprovado pelo usuário na definição do módulo; princípios e escopo abaixo resumem os requisitos aplicáveis.

## 1. Visão e princípio central
O Dossiers organiza, armazena, relaciona e apresenta informações sobre pessoas, empresas, grupos econômicos, holdings, instituições e outras entidades relevantes, transformando informações dispersas em dossiês estruturados, rastreáveis e continuamente atualizáveis.

**Princípio:** o SCOUT preserva contexto, origem, validade e grau de confiança de cada informação. Informação registrada não é automaticamente verdadeira; inferências não são promovidas a fato sem fluxo explícito.

## 2. Escopo funcional (V1.0)
1. **Entity Profiles** (D1) — cadastro/consulta/edição/pesquisa/detecção de duplicidades, perfis e página individual.
2. **Research & Evidence** (D2) — informações com classificação epistemológica, fontes, evidências, confiança, histórico.
3. **Relationship History** (D3) — interações, linha do tempo, distinção declarado/observado/interpretado/a confirmar.
4. **Connections** (D4) — relações entre entidades, temporalidade, evidências, visualização simplificada.
5. **Strategic Insights** (D5) — hipóteses/oportunidades com fundamentação e estados, sem execução automática.

## 3. Requisitos transversais
- Reutilizar Foundation e estruturas existentes (entities, relationships, claims, evidence, sources, documents, raw_records, data_changes, audit_events etc.) sem duplicação.
- Persistência local (SQLite/Alembic), integridade referencial, migrações versionadas, proveniência e rastreabilidade.
- UI de consulta/análise (não apenas formulários), pesquisa local, estados claros, sem simulação de dados/funcionalidades.
- Funcionalidades determinísticas primeiro; integração futura com IA local (Ollama) opcional, sob demanda, sem promover inferências a fatos.
- Segurança/privacidade local, minimização de dados, tratamento de conteúdo externo como dado não confiável.
- Implementação incremental por subetapas autorizadas, com testes e documentação.

## 4. Estado de implementação
- **D1 — Entity Profiles:** implementado nesta entrega (modelagem aditiva, CRUD/pesquisa/filtros, duplicidades sugeridas sem fusão automática, UI home e página da entidade com seções futuras não simuladas).
- **D2–D6:** pendentes de autorização/implementação.
