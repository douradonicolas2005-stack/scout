import { Bot } from "lucide-react";
import { ModulePlaceholder } from "./ModulePlaceholder";

export function AgentControlPage() {
  return (
    <ModulePlaceholder
      title="Agent Control"
      description="Orquestração, agentes e execuções de inteligência."
      icon={Bot}
      capabilities={["Configuração de agentes e modelos locais (Ollama)", "Registro de execuções (agent_runs)", "Políticas de uso sob demanda e controle humano"]}
    />
  );
}
