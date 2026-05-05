import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { setApiBaseUrl } from "@/lib/api";

interface AppConfig {
  apiBaseUrl: string;
  setApiBaseUrl: (v: string) => void;
  pollInterval: number;
  setPollInterval: (v: number) => void;
}

const STORAGE_KEY = "kaavach.config";
const DEFAULTS = { apiBaseUrl: "http://localhost:8000", pollInterval: 2500 };

const AppConfigContext = createContext<AppConfig | null>(null);

function load() {
  if (typeof window === "undefined") return DEFAULTS;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULTS;
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return DEFAULTS;
  }
}

export function AppConfigProvider({ children }: { children: ReactNode }) {
  const [apiBaseUrl, setUrl] = useState(DEFAULTS.apiBaseUrl);
  const [pollInterval, setPoll] = useState(DEFAULTS.pollInterval);

  useEffect(() => {
    const cfg = load();
    setUrl(cfg.apiBaseUrl);
    setPoll(cfg.pollInterval);
    setApiBaseUrl(cfg.apiBaseUrl);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ apiBaseUrl, pollInterval }));
    setApiBaseUrl(apiBaseUrl);
  }, [apiBaseUrl, pollInterval]);

  const value = useMemo<AppConfig>(
    () => ({
      apiBaseUrl,
      setApiBaseUrl: setUrl,
      pollInterval,
      setPollInterval: setPoll,
    }),
    [apiBaseUrl, pollInterval],
  );

  return <AppConfigContext.Provider value={value}>{children}</AppConfigContext.Provider>;
}

export function useAppConfig() {
  const ctx = useContext(AppConfigContext);
  if (!ctx) throw new Error("useAppConfig must be used within AppConfigProvider");
  return ctx;
}
