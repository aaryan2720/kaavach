import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAppConfig } from "@/context/AppConfigContext";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Activity } from "lucide-react";

export function TopBar() {
  const { apiBaseUrl, setApiBaseUrl } = useAppConfig();
  const [draft, setDraft] = useState(apiBaseUrl);

  useEffect(() => setDraft(apiBaseUrl), [apiBaseUrl]);

  // Debounced save
  useEffect(() => {
    const t = setTimeout(() => {
      if (draft && draft !== apiBaseUrl) setApiBaseUrl(draft);
    }, 500);
    return () => clearTimeout(t);
  }, [draft, apiBaseUrl, setApiBaseUrl]);

  const health = useQuery({
    queryKey: ["health", apiBaseUrl],
    queryFn: api.health,
    refetchInterval: 5000,
    retry: 1,
  });

  const ok = health.isSuccess;
  const status = health.isLoading ? "checking" : ok ? "online" : "offline";
  const variant: Record<string, string> = {
    online: "bg-success/15 text-success border-success/30",
    offline: "bg-destructive/15 text-destructive border-destructive/30",
    checking: "bg-muted text-muted-foreground border-border",
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-3 backdrop-blur sm:px-4">
      <SidebarTrigger />
      <div className="flex flex-1 items-center gap-3">
        <div className="hidden items-center gap-2 sm:flex">
          <Activity className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">Kaavach IDS</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <label className="hidden text-xs text-muted-foreground md:block" htmlFor="api-base">
            API
          </label>
          <Input
            id="api-base"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="http://localhost:8000"
            className="h-8 w-48 font-mono text-xs sm:w-72"
            spellCheck={false}
          />
          <Badge
            variant="outline"
            className={`gap-1.5 capitalize ${variant[status]}`}
            aria-live="polite"
          >
            <span
              className={`pulse-dot inline-block h-1.5 w-1.5 rounded-full ${
                ok ? "text-success" : status === "checking" ? "text-muted-foreground" : "text-destructive"
              }`}
              style={{ background: "currentColor" }}
            />
            {status}
          </Badge>
        </div>
      </div>
    </header>
  );
}
