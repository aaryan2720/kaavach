import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { useAppConfig } from "@/context/AppConfigContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — Kaavach IDS" },
      { name: "description", content: "Configure API base URL and polling preferences." },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const cfg = useAppConfig();
  const [api, setApi] = useState(cfg.apiBaseUrl);
  const [poll, setPoll] = useState(cfg.pollInterval);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Persisted to localStorage.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Connection</CardTitle>
          <CardDescription>Backend API endpoint for the Kaavach service.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="api">API Base URL</Label>
            <Input
              id="api"
              value={api}
              onChange={(e) => setApi(e.target.value)}
              className="font-mono"
              placeholder="http://localhost:8000"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="poll">Poll interval (ms)</Label>
            <Input
              id="poll"
              type="number"
              min={500}
              step={250}
              value={poll}
              onChange={(e) => setPoll(Number(e.target.value))}
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">
              How often to refetch live events. Recommended 2000–3000ms.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => {
                cfg.setApiBaseUrl(api.trim());
                cfg.setPollInterval(Math.max(500, Number(poll) || 2500));
                toast.success("Settings saved");
              }}
            >
              Save
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setApi("http://localhost:8000");
                setPoll(2500);
              }}
            >
              Reset defaults
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
