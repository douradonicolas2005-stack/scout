import { Link, useLocation } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { NAV_ITEMS } from "@/app/routes";

export function Breadcrumbs() {
  const { pathname } = useLocation();
  const current = NAV_ITEMS.find((i) => pathname.startsWith(i.path));

  return (
    <nav
      aria-label="Breadcrumb"
      className="flex min-w-0 items-center gap-1 text-sm text-muted-foreground"
    >
      <Link to="/" className="shrink-0 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm">
        SCOUT
      </Link>
      <ChevronRight className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      {current ? (
        <span className="truncate font-medium text-foreground" aria-current="page">
          {current.label}
        </span>
      ) : (
        <span className="truncate font-medium text-foreground" aria-current="page">
          Foundation
        </span>
      )}
    </nav>
  );
}
