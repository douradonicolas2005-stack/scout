import { FolderSearch } from "lucide-react";
import { ModulePlaceholder } from "./ModulePlaceholder";

export function DossiersPage() {
  return (
    <ModulePlaceholder
      title="Dossiers"
      description="Dossiês e consolidação de contexto por entidade."
      icon={FolderSearch}
      capabilities={["Perfis e dossiês de entidades", "Histórico de evidências e documentos", "Rastreabilidade de procedência"]}
    />
  );
}
