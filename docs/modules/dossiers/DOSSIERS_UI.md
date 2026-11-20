# DOSSIERS — UI (D1: Entity Profiles, D2: Research & Evidence)

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
  3. **Histórico** — placeholder informativo (D3), sem simulação.
  4. **Relações** — placeholder informativo (D4), sem simulação.
  5. **Pesquisa e evidências (D2)** — Research Workspace funcional (ver seção 3).
  6. **Insights** — placeholder informativo (D5), sem simulação.
- **Duplicidades:** painel com candidatos sugeridos, nível indicativo e motivos; somente navegação/consulta, **sem fusão automática**.

## 3. Research Workspace (D2)
Implementado na seção “Pesquisa e evidências” da página da entidade, com consumo real da API e sem simulação:
- **Resumo:** indicadores determinísticos persistidos/derivados (documentos, fontes referenciadas, afirmações, evidências, afirmações pendentes de verificação, conflitos abertos/em análise, distribuições por tipo/verificação).
- **Documentos:** listagem por entidade, registro manual com metadados/proveniência (localizador/origem e/ou fonte de pesquisa, tipo, verificação, referência-only), estados e exibição de origem/rastreabilidade básica.
- **Fontes de pesquisa:** catálogo/listagem e cadastro de fontes consultadas (nome, tipo, URL/domínio, confiabilidade/justificativa, verificação).
- **Afirmações & evidências:** registro de afirmações com classificação epistemológica, verificação, confiança/justificativa e datas/proveniência; adição de evidências vinculadas à afirmação (relação suporta/contesta/contextualiza, âncoras/localização/trechos). Rotulagem clara: afirmações não são fatos automaticamente e inferências não são promovidas sem ação explícita.
- **Conflitos:** registro e listagem de conflitos entre afirmações (tipo/status/descrição), sem resolução automática.
- **Estados:** carregamento, erro, vazio e feedback de submissão.

## 4. Formulário de entidade (D1)
- Criação/edição por tipo: pessoa, empresa, grupo econômico/holding, instituição, outro.
- Campos: nome principal, nomes alternativos, descrição, localização, status do perfil, verificação, identificadores, atributos estruturados em `profile_data` e observações.

## 5. Design e acessibilidade
- Reuso do Design System SCOUT (tokens, temas, componentes `shared`/`ui`, App Shell/breadcrumbs existentes).
- Hierarquia clara, baixa densidade desnecessária, estados vazios elaborados, acessibilidade básica (labels, foco, teclado).
- Sem reconstrução do App Shell e sem simulação de dados/funcionalidades futuras (D3–D5).
