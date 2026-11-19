import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  badge?: string;
  actions?: ReactNode;
}

export function PageHeader({ title, description, icon, badge, actions }: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          {icon ? <span className="text-primary">{icon}</span> : null}
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          {badge ? <Badge variant="outline">{badge}</Badge> : null}
        </div>
        {description ? <p className="max-w-3xl text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}
