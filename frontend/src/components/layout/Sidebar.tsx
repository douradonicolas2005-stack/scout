import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "@/app/routes";
import { cn } from "@/lib/utils";

interface SidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export function Sidebar({ className, onNavigate }: SidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full w-64 shrink-0 flex-col border-r border-border bg-card/40",
        className
      )}
    >
      <div className="flex h-14 items-center border-b border-border px-4">
        <div className="flex items-center gap-2">
          <div
            className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground"
            aria-hidden="true"
          >
            S
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold tracking-wide">SCOUT</div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
              Strategic Intelligence
            </div>
          </div>
        </div>
      </div>

      <nav aria-label="Navegação principal" className="flex-1 space-y-0.5 overflow-y-auto p-2">
        <NavLink
          to="/"
          end
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              isActive
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            )
          }
        >
          <span className="flex h-4 w-4 shrink-0 items-center justify-center text-[10px] font-semibold" aria-hidden="true">F</span>
          <span className="truncate">Foundation</span>
        </NavLink>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span className="truncate">{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="border-t border-border p-3 text-[11px] text-muted-foreground">
        Foundation V1.1 · local (loopback)
      </div>
    </aside>
  );
}
