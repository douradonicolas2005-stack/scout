# DOSSIERS — UI (D1: Entity Profiles, D2: Research & Evidence, D3: Relationship History)

## 1. Home (`/dossiers`)
Página de entrada orientada a pesquisa/navegação (sem dashboard pesado).
- **Pesquisa:** campo de busca local (nome, alternativo, identificador) com filtros (tipo, status do perfil, verificação, período de atualização) e ordenação.
- **Resultados/listagem:** entidades com tipo, status, verificação e última atualização; navegação para o dossiê.
- **Blocos contextuais (dados reais):** entidades recentemente atualizadas e recém-criadas (API); “recentemente consultadas” mantido localmente no cliente (localStorage) sem simulação.
- **Ações:** criar nova entidade; acessar detalhe.
- **Estados:** carregamento, erro, vazio, sucesso.

## 2. Página da entidade (`/dossiers/:entityId`)
- **Cabeçalho:** nome, tipo, identificadores relevantes, descrição curta, estado de verificação, última atualização; ações de edição e consulta de duplicidades sugeridas.
- **Seções (navegação sem perder contexto):**
  1. **Visão geral** — resumo cadastral, localização, metadados (criação/atualização, origem quando aplicável).
  2. **Informações** — atributos/`profile_data` por tipo, identificadores, aliases, observações.
  3. **Histórico (D3)** — linha do tempo de interações (funcional, ver seção 4).
  4. **Relações** — placeholder informativo (D4 — Connections), sem simulação.
  5. **Pesquisa e evidências (D2)** — Research Workspace funcional (ver seção 3).
  6. **Insights** — placeholder informativo (D5 — Strategic Insights), sem simulação.
- **Duplicidades:** painel com candidatos sugeridos, nível indicativo e motivos; somente navegação/consulta, **sem fusão automática**.

## 3. Research Workspace (D2)
Implementado na seção “Pesquisa e evidências”, com consumo real da API e sem simulação:
- **Resumo:** indicadores determinísticos (documentos, fontes referenciadas, afirmações, evidências, pendências de verificação, conflitos abertos/em análise, distribuições).
- **Documentos:** listagem e registro manual com metadados/proveniência (âncora/origem e/ou fonte de pesquisa), estados e rastreabilidade básica.
- **Fontes de pesquisa:** catálogo/listagem e cadastro de fontes consultadas (confiabilidade/justificativa, verificação).
- **Afirmações & evidências:** registro com classificação epistemológica, verificação, confiança/justificativa e datas/proveniência; evidências com relação suporta/contesta/contextualiza e âncoras. Rotulagem clara: afirmações não são fatos automaticamente e inferências não são promovidas sem ação explícita.
- **Conflitos:** registro e listagem de conflitos entre afirmações (tipo/status/descrição), sem resolução automática.
- **Estados:** carregamento, erro, vazio e feedback de submissão.

## 4. History Workspace (D3 — Relationship History)
Implementado na seção **Histórico** (`frontend/src/components/dossiers/HistoryWorkspace.tsx`), com consumo real da API e sem simulação:
- **Resumo determinístico:** contagens (interações, pendentes a confirmar/revisão), distribuições por natureza/tipo/status e período de ocorrências registradas.
- **Linha do tempo/listagem:** itens cronológicos com tipo, título, natureza (`declarado`, `observado`, `interpretado`, `a confirmar`) e status rotulados, data/precisão temporal, canal/local e indicadores de contexto/proveniência.
- **Filtros e ordenação:** busca textual, tipo, natureza, status e ordenação (ex.: ocorrência desc/asc).
- **Registro e detalhe:** formulário de criação com campos de conteúdo, temporalidade, contexto, proveniência/referências opcionais (IDs/locators) e justificativa; painel de detalhe com metadados/proveniência e ações explícitas de atualização de estado (rastreáveis). Interpretações não são promovidas a fato automaticamente.
- **Estados:** carregamento, erro, vazio e feedback de submissão.

## 5. Formulário de entidade (D1)
- Criação/edição por tipo: pessoa, empresa, grupo econômico/holding, instituição, outro.
- Campos: nome principal, nomes alternativos, descrição, localização, status do perfil, verificação, identificadores, atributos estruturados em `profile_data` e observações.

## 6. Design e acessibilidade
- Reuso do Design System SCOUT (tokens, temas, componentes `shared`/`ui`, App Shell/breadcrumbs existentes).
- Hierarquia clara, baixa densidade desnecessária, estados vazios elaborados, acessibilidade básica (labels, foco, teclado).
- Sem reconstrução do App Shell e sem simulação de dados/funcionalidades futuras (D4–D5 permanecem placeholders).
