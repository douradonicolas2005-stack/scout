import { Menu, Moon, Sun } from "lucide-react";
import { Breadcrumbs } from "./Breadcrumbs";
import { GlobalSearch } from "./GlobalSearch";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/app/store/app-store";

export function Header() {
  const theme = useAppStore((s) => s.theme);
  const toggleTheme = useAppStore((s) => s.toggleTheme);
  const toggleMobileNav = useAppStore((s) => s.toggleMobileNav);

  return (
    <header className="flex h-14 items-center justify-between gap-3 border-b border-border bg-background/95 px-3 backdrop-blur supports-[backdrop-filter]:bg-background/70 sm:px-4">
      <div className="flex min-w-0 items-center gap-2">
        <Button
          variant="outline"
          size="icon"
          className="md:hidden"
          onClick={toggleMobileNav}
          aria-label="Abrir navegação"
          title="Menu"
        >
          <Menu className="h-4 w-4" />
        </Button>
        <Breadcrumbs />
      </div>
      <div className="flex flex-1 items-center justify-end gap-2">
        <GlobalSearch />
        <Button
          variant="outline"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro"}
          title={theme === "dark" ? "Tema claro" : "Tema escuro"}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </header>
  );
}
