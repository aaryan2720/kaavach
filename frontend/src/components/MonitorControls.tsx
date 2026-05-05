import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { Play, Square, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function MonitorControls() {
  const qc = useQueryClient();
  const status = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: 4000,
    retry: 1,
  });

  const running = !!status.data?.running;
  const backendOk = status.data?.backend_available !== false;
  const buffered = status.data?.buffered_events ?? 0;

  const start = useMutation({
    mutationFn: api.start,
    onMutate: () => {
      qc.setQueryData(["status"], (old: unknown) => ({ ...(old as object), running: true }));
    },
    onSuccess: () => {
      toast.success("Monitor started");
      qc.invalidateQueries({ queryKey: ["status"] });
    },
    onError: (e: Error) => {
      toast.error(`Failed to start: ${e.message}`);
      qc.invalidateQueries({ queryKey: ["status"] });
    },
  });

  const stop = useMutation({
    mutationFn: api.stop,
    onMutate: () => {
      qc.setQueryData(["status"], (old: unknown) => ({ ...(old as object), running: false }));
    },
    onSuccess: () => {
      toast.success("Monitor stopped");
      qc.invalidateQueries({ queryKey: ["status"] });
    },
    onError: (e: Error) => {
      toast.error(`Failed to stop: ${e.message}`);
      qc.invalidateQueries({ queryKey: ["status"] });
    },
  });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["status"] });
    qc.invalidateQueries({ queryKey: ["events"] });
    toast.message("Refreshed");
  };

  // Keyboard shortcuts: R refresh, S start/stop toggle
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || (e.target as HTMLElement)?.isContentEditable)
        return;
      if (e.key === "r" || e.key === "R") {
        e.preventDefault();
        refresh();
      } else if (e.key === "s" || e.key === "S") {
        e.preventDefault();
        if (running) stop.mutate();
        else start.mutate();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running]);

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center gap-3 p-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Monitor</span>
          <Badge
            variant="outline"
            className={
              running
                ? "border-success/30 bg-success/15 text-success"
                : "border-muted-foreground/30 bg-muted text-muted-foreground"
            }
            aria-live="polite"
          >
            <span
              className="pulse-dot mr-1.5 inline-block h-1.5 w-1.5 rounded-full"
              style={{ background: "currentColor" }}
            />
            {running ? "Running" : "Stopped"}
          </Badge>
          <Badge
            variant="outline"
            className={
              backendOk
                ? "border-border text-muted-foreground"
                : "border-warning/30 bg-warning/10 text-warning"
            }
          >
            Backend: {backendOk ? "available" : "unavailable"}
          </Badge>
          <Badge variant="outline" className="border-border text-muted-foreground">
            Buffered: {buffered}
          </Badge>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <Button
            size="sm"
            onClick={() => start.mutate()}
            disabled={running || start.isPending}
            aria-label="Start monitor (S)"
          >
            <Play className="mr-1.5 h-3.5 w-3.5" /> Start
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => stop.mutate()}
            disabled={!running || stop.isPending}
            aria-label="Stop monitor (S)"
          >
            <Square className="mr-1.5 h-3.5 w-3.5" /> Stop
          </Button>
          <Button size="sm" variant="outline" onClick={refresh} aria-label="Refresh (R)">
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
