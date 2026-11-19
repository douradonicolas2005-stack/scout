import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { RadarPage } from "@/pages/RadarPage";
import { DossiersPage } from "@/pages/DossiersPage";
import { KnowledgeGraphPage } from "@/pages/KnowledgeGraphPage";
import { PredictionsPage } from "@/pages/PredictionsPage";
import { ScenarioLabPage } from "@/pages/ScenarioLabPage";
import { ActionCenterPage } from "@/pages/ActionCenterPage";
import { AgentControlPage } from "@/pages/AgentControlPage";
import { SystemPage } from "@/pages/SystemPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="radar" element={<RadarPage />} />
        <Route path="dossiers" element={<DossiersPage />} />
        <Route path="knowledge-graph" element={<KnowledgeGraphPage />} />
        <Route path="predictions" element={<PredictionsPage />} />
        <Route path="scenario-lab" element={<ScenarioLabPage />} />
        <Route path="action-center" element={<ActionCenterPage />} />
        <Route path="agent-control" element={<AgentControlPage />} />
        <Route path="system" element={<SystemPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
