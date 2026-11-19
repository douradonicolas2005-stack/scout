import type { LucideIcon } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { PageState } from "@/components/shared/PageState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  title: string;
  description: string;
  icon: LucideIcon;
  capabilities?: string[];
}

export function ModulePlaceholder({ title, description, icon: Icon, capabilities = [] }: Props) {
  return (
    <div className="space-y-4">
      <PageHeader
        title={title}
        description={description}
        icon={<Icon className="h-5 w-5" />}
        badge="Em desenvolvimento"
      />
      <PageState
        kind="development"
        title="Módulo ainda não implementado"
        description="Esta área faz parte da arquitetura do SCOUT, mas sua funcionalidade não está disponível na Foundation V1.1. Nenhum dado, conexão ou processamento é simulado nesta tela."
      />
      {capabilities.length > 0 ? (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Escopo previsto (fases futuras)</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              {capabilities.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
