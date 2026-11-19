import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Bot,
  FolderSearch,
  LayoutGrid,
  LineChart,
  Network,
  Radar,
  Settings,
} from "lucide-react";

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  description: string;
  implemented: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  {
    path: "/radar",
    label: "Radar",
    icon: Radar,
    description: "Monitoramento e sinais estratégicos prioritários.",
    implemented: false,
  },
  {
    path: "/dossiers",
    label: "Dossiers",
    icon: FolderSearch,
    description: "Dossiês e consolidação de contexto por entidade.",
    implemented: false,
  },
  {
    path: "/knowledge-graph",
    label: "Knowledge Graph",
    icon: Network,
    description: "Grafo de conhecimento, entidades e relacionamentos.",
    implemented: false,
  },
  {
    path: "/predictions",
    label: "Predictions",
    icon: LineChart,
    description: "Modelos, previsões e séries temporais.",
    implemented: false,
  },
  {
    path: "/scenario-lab",
    label: "Scenario Lab",
    icon: LayoutGrid,
    description: "Simulações e análise de cenários.",
    implemented: false,
  },
  {
    path: "/action-center",
    label: "Action Center",
    icon: Activity,
    description: "Ações, aprovações e acompanhamento operacional.",
    implemented: false,
  },
  {
    path: "/agent-control",
    label: "Agent Control",
    icon: Bot,
    description: "Orquestração, agentes e execuções de inteligência.",
    implemented: false,
  },
  {
    path: "/system",
    label: "System",
    icon: Settings,
    description: "Configuração, fontes, auditoria e estado da plataforma.",
    implemented: false,
  },
];
