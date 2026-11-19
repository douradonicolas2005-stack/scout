import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";

export function GlobalSearch() {
  return (
    <div className="relative w-full max-w-[14rem] sm:max-w-xs md:max-w-sm">
      <Search
        className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden="true"
      />
      <Input
        type="search"
        placeholder="Pesquisa global (em breve)"
        className="h-9 pl-8"
        aria-label="Pesquisa global (em breve)"
        title="Pesquisa global indisponível nesta etapa"
        disabled
        readOnly
      />
    </div>
  );
}
