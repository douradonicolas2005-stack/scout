import { Activity } from "lucide-react";
import { ModulePlaceholder } from "./ModulePlaceholder";

export function ActionCenterPage() {
  return (
    <ModulePlaceholder
      title="Action Center"
      description="Ações, aprovações e acompanhamento operacional."
      icon={Activity}
      capabilities={["Fila de ações com controle humano", "Aprovações e permissões", "Histórico e auditoria de decisões"]}
    />
  );
}
