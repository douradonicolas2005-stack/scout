import { Network } from "lucide-react";
import { ModulePlaceholder } from "./ModulePlaceholder";

export function KnowledgeGraphPage() {
  return (
    <ModulePlaceholder
      title="Knowledge Graph"
      description="Grafo de conhecimento, entidades e relacionamentos."
      icon={Network}
      capabilities={["Visualização de entidades e relações", "Navegação por evidências vinculadas", "Exploração temporal e por confiança"]}
    />
  );
}
