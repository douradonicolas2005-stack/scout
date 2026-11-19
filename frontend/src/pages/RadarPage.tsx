import { Radar } from "lucide-react";
import { ModulePlaceholder } from "./ModulePlaceholder";

export function RadarPage() {
  return (
    <ModulePlaceholder
      title="Radar"
      description="Monitoramento e sinais estratégicos prioritários."
      icon={Radar}
      capabilities={["Priorização de sinais e alertas", "Visão consolidada de mudanças relevantes", "Integração com fontes e evidências rastreáveis"]}
    />
  );
}
