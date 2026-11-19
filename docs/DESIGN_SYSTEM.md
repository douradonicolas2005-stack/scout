# DESIGN_SYSTEM — SCOUT (Foundation V1.1)

> **Status:** consolidado na Subetapa H (base C mantida, integração D e monitoramento operacional mínimo G alinhados; sem simulação de funcionalidades).

## Identidade visual e tokens (paleta SCOUT)

Paleta obrigatória aplicada via variáveis CSS HSL em `frontend/src/styles/globals.css` (com espelhos `--scout-*`) e mapeada no Tailwind:

| Token SCOUT | Hex | Uso principal |
|---|---|---|
| Navy | `#0A192F` | Base/fundo escuro, texto em tema claro |
| Navy 2 | `#14243A` | Superfícies/cartões em tema escuro |
| Teal | `#26767A` | Primário (tema claro) |
| Teal 2 | `#36979C` | Primário/destaque e ring (tema escuro) |
| Gold | `#C5A059` | Acento (ênfase controlada) |
| Gray | `#E8EDF2` | Texto/superfícies suaves (tema escuro) |
| Slate | `#94A3B8` | Apoio/muted |
| Ice | `#F5F7FA` | Fundo e texto primário sobre teal (tema claro) |

Tokens semânticos: `background`, `foreground`, `card`, `primary`, `secondary`, `muted`, `accent`, `destructive`, `border`, `input`, `ring` (+ `*-foreground`).

## Temas
- **Modos:** claro e escuro, controlados por classe no `html` (`.dark`/`.light`) e tokens CSS.
- **Padrão:** escuro.
- **Persistência:** `localStorage` chave `scout-theme` (`app/store/app-store.ts`).
- **Bootstrap sem flash:** script inline em `frontend/index.html` aplica o tema antes da hidratação.

## App Shell e navegação
- **Layout:** `AppShell` (`components/layout/AppShell.tsx`) com Sidebar, Header e área principal responsiva (`main#main-content`).
- **Sidebar (`components/layout/Sidebar.tsx`):** marca SCOUT, navegação principal (Foundation + 8 áreas), estado ativo via `NavLink`, rodapé de contexto local; recolhe em drawer/modal em telas pequenas.
- **Header (`components/layout/Header.tsx`):** acionador de menu mobile, breadcrumbs, pesquisa global integrada (placeholder), alternância de tema.
- **Breadcrumbs (`components/layout/Breadcrumbs.tsx`):** `SCOUT / <área atual>` com indicação de página atual (`aria-current`).
- **Pesquisa global (`components/layout/GlobalSearch.tsx`):** campo sempre presente e **desabilitado** ("Pesquisa global (em breve)") — sem simular busca ou resultados.
- **Responsividade:** sidebar fixa em `md+`, drawer com overlay/fechamento por clique, navegação ou `Esc` em mobile.
- **Acessibilidade básica:** link "Pular para o conteúdo", `nav` rotulado, foco visível (`focus-visible` ring), labels/aria em controles e estados.

## Áreas funcionais e navegação (8 + Foundation)
Rotas consistentes: **Radar**, **Dossiers**, **Knowledge Graph**, **Predictions**, **Scenario Lab**, **Action Center**, **Agent Control**, **System**. **Foundation** (Dashboard) e **System** consomem estado/contratos reais do backend; as demais 7 áreas permanecem placeholders (`ModulePlaceholder`) em estado “em desenvolvimento”, sem dados, conexões ou processamento simulados.

## Estados e padrões de interação
- **Estados padronizados:** `development`, `empty`, `loading`, `error`, `info` (`PageState`) com semântica de status (`role/aria-live/aria-busy`) apropriada.
- **Feedback operacional (System, Subetapa G):** ações reais suportadas pelo backend (teste de conexão, criação/execução de jobs, atualização/inspeção de runs/eventos/auditoria) com feedback de resultado/erro e recarga de dados — sem simulação.
- **PageHeader:** ícone, título, descrição, badge e ações.

## Componentes base (shadcn/ui) e compartilhados
- **Primitivas (`components/ui`):** `Button` (variantes/tamanhos, foco e disabled), `Card` (+ Header/Title/Description/Content), `Badge`, `Input`.
- **Compartilhados (`components/shared`):** `PageHeader`, `PageState`.
- **Padrão de módulo:** `ModulePlaceholder` para áreas não implementadas.

## Organização frontend (camadas/features)
- `app/` (App, rotas, store Zustand), `components/{ui,layout,shared}`, `pages/`, `features/*` (reservado por área para evolução), `lib/api` (cliente/tipos), `lib/utils`, `styles/globals.css`, `hooks/` (reservado).
- Integração de dados: `health`, `system/info`, `db/status` e contratos de ingestão/monitoramento/auditoria conforme escopo implementado.
