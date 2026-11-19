import { create } from "zustand";

export type ThemeMode = "light" | "dark";

interface AppState {
  theme: ThemeMode;
  mobileNavOpen: boolean;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  setMobileNavOpen: (open: boolean) => void;
  toggleMobileNav: () => void;
}

const THEME_KEY = "scout-theme";

function getInitialTheme(): ThemeMode {
  if (typeof window === "undefined") return "dark";
  try {
    const stored = window.localStorage.getItem(THEME_KEY);
    return stored === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

function applyTheme(theme: ThemeMode) {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.classList.toggle("light", theme === "light");
  try {
    window.localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* ignore */
  }
}

const initialTheme = getInitialTheme();

export const useAppStore = create<AppState>((set, get) => ({
  theme: initialTheme,
  mobileNavOpen: false,
  setTheme: (theme) => {
    applyTheme(theme);
    set({ theme });
  },
  toggleTheme: () => {
    const next = get().theme === "dark" ? "light" : "dark";
    applyTheme(next);
    set({ theme: next });
  },
  setMobileNavOpen: (open) => set({ mobileNavOpen: open }),
  toggleMobileNav: () => set((s) => ({ mobileNavOpen: !s.mobileNavOpen })),
}));

// ensure DOM reflects store on load (index.html pre-applies to avoid flash)
if (typeof window !== "undefined") {
  applyTheme(initialTheme);
}
