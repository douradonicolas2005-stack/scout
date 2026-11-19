import type { ReactNode } from "react";
import { AlertCircle, CircleDashed, Construction, Inbox, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type StateKind = "development" | "empty" | "loading" | "error" | "info";

interface PageStateProps {
  kind: StateKind;
  title: string;
  description?: string;
  className?: string;
  children?: ReactNode;
}

const config: Record<StateKind, { icon: typeof Construction; tone: string }> = {
  development: { icon: Construction, tone: "text-accent" },
  empty: { icon: Inbox, tone: "text-muted-foreground" },
  loading: { icon: Loader2, tone: "text-primary" },
  error: { icon: AlertCircle, tone: "text-destructive" },
  info: { icon: CircleDashed, tone: "text-muted-foreground" },
};

export function PageState({ kind, title, description, className, children }: PageStateProps) {
  const { icon: Icon, tone } = config[kind];
  const live = kind === "error" ? "assertive" : kind === "loading" ? "polite" : undefined;
  const role = kind === "error" || kind === "loading" ? "status" : undefined;

  return (
    <Card className={cn("border-dashed", className)}>
      <CardContent
        className="flex flex-col items-center justify-center gap-2 py-12 text-center"
        role={role}
        aria-live={live}
        aria-busy={kind === "loading" ? true : undefined}
      >
        <Icon
          className={cn("h-8 w-8", tone, kind === "loading" && "animate-spin")}
          aria-hidden="true"
        />
        <h2 className="text-base font-medium">{title}</h2>
        {description ? (
          <p className="max-w-xl text-sm text-muted-foreground">{description}</p>
        ) : null}
        {children ? <div className="mt-2">{children}</div> : null}
      </CardContent>
    </Card>
  );
}
