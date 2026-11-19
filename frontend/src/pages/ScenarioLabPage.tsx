import { LayoutGrid } from "lucide-react";
import { ModulePlaceholder } from "./ModulePlaceholder";

export function ScenarioLabPage() {
  return (
    <ModulePlaceholder
      title="Scenario Lab"
      description="Simulações e análise de cenários."
      icon={LayoutGrid}
      capabilities={["Construção e comparação de cenários", "Simulações com premissas rastreáveis", "Avaliação de impactos e incertezas"]}
    />
  );
}
