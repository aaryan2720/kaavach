import { useMemo, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { List, type RowComponentProps } from "react-window";
import { api } from "@/lib/api";
import { useAppConfig } from "@/context/AppConfigContext";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  formatTimeUTC,
  getConfidence,
  getDecision,
  getDst,
  getDstPort,
  getEventTime,
  getLength,
  getProto,
  getSrc,
  getSrcPort,
  isAttack,
} from "@/lib/event-utils";
import type { NetworkEvent } from "@/lib/types";

const COLS = "120px 1fr 60px 1fr 60px 60px 65px 70px 1fr";

interface RowData {
  events: NetworkEvent[];
}

function Row({ index, style, events }: RowComponentProps<RowData>) {
  const e = events[index];
  if (!e) return null;
  const attack = isAttack(e);
  const conf = getConfidence(e);
  const decision = getDecision(e);
  return (
    <div
      style={{ ...style, display: "grid", gridTemplateColumns: COLS }}
      className={`items-center gap-2 border-b border-border/60 px-3 text-xs ${
        attack ? "bg-destructive/10 text-destructive-foreground" : "hover:bg-muted/40"
      }`}
      role="row"
    >
      <div className="font-mono text-muted-foreground">{formatTimeUTC(getEventTime(e))}</div>
      <div className="truncate font-mono">{getSrc(e)}</div>
      <div className="font-mono text-[10px] text-muted-foreground">{getSrcPort(e)}</div>
      <div className="truncate font-mono">{getDst(e)}</div>
      <div className="font-mono text-[10px] text-muted-foreground">{getDstPort(e)}</div>
      <div className="font-mono uppercase">{getProto(e)}</div>
      <div className="font-mono text-[10px] text-muted-foreground">{getLength(e)}</div>
      <div>
        <span
          className={`inline-flex rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
            attack ? "bg-destructive text-destructive-foreground" : "bg-success/20 text-success"
          }`}
        >
          {decision}
        </span>
      </div>
      <div className="font-mono">{conf != null ? `${(conf * 100).toFixed(0)}%` : "—"}</div>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="truncate text-muted-foreground">{e.reason || "—"}</div>
          </TooltipTrigger>
          {e.reason && (
            <TooltipContent side="left" className="max-w-xs">
              <p className="text-xs">{e.reason}</p>
            </TooltipContent>
          )}
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}

function MobileCard({ e }: { e: NetworkEvent }) {
  const attack = isAttack(e);
  const conf = getConfidence(e);
  return (
    <div
      className={`rounded-md border p-3 text-xs ${
        attack ? "border-destructive/40 bg-destructive/10" : "border-border bg-card"
      }`}
    >
      <div className="flex items-center justify-between">
        <span
          className={`inline-flex rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
            attack ? "bg-destructive text-destructive-foreground" : "bg-success/20 text-success"
          }`}
        >
          {getDecision(e)}
        </span>
        <span className="font-mono text-muted-foreground">{formatTimeUTC(getEventTime(e))}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-1 font-mono">
        <span className="text-muted-foreground">src</span>
        <span className="truncate text-right">{getSrc(e)}</span>
        <span className="text-muted-foreground">dst</span>
        <span className="truncate text-right">{getDst(e)}</span>
        <span className="text-muted-foreground">proto</span>
        <span className="text-right uppercase">{getProto(e)}</span>
        <span className="text-muted-foreground">conf</span>
        <span className="text-right">{conf != null ? `${(conf * 100).toFixed(1)}%` : "—"}</span>
      </div>
      {e.reason && <p className="mt-2 text-muted-foreground">{e.reason}</p>}
    </div>
  );
}

export function LiveEventsTable() {
  const { pollInterval } = useAppConfig();
  const containerRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["events"],
    queryFn: () => api.events(300),
    refetchInterval: pollInterval,
    retry: (count) => count < 3,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 15000),
  });

  const events = useMemo(() => data ?? [], [data]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div>
          <CardTitle className="text-base">Live Events</CardTitle>
          <CardDescription>
            {isLoading ? "Loading…" : `${events.length} recent events`}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isError && (
          <div className="px-4 py-3 text-sm text-destructive">
            Failed to load events: {(error as Error)?.message}
          </div>
        )}

        {/* Desktop virtualized table */}
        <div className="hidden md:block">
          <div
            className="grid border-y border-border bg-muted/40 px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
            style={{ gridTemplateColumns: COLS }}
            role="row"
          >
            <span>Time (UTC)</span>
            <span>Source</span>
            <span>S Port</span>
            <span>Destination</span>
            <span>D Port</span>
            <span>Proto</span>
            <span>Length</span>
            <span>Decision</span>
            <span>Conf.</span>
            <span>Reason</span>
          </div>
          <div ref={containerRef} className="h-[480px]">
            {events.length === 0 && !isLoading ? (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                No events yet.
              </div>
            ) : (
              <List
                rowCount={events.length}
                rowHeight={36}
                rowComponent={Row}
                rowProps={{ events }}
                style={{ height: 480 }}
              />
            )}
          </div>
        </div>

        {/* Mobile cards */}
        <div className="space-y-2 p-3 md:hidden">
          {events.length === 0 && !isLoading ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No events yet.</p>
          ) : (
            events.slice(0, 50).map((e, i) => <MobileCard key={i} e={e} />)
          )}
        </div>
      </CardContent>
    </Card>
  );
}
