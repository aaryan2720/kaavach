import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Download, FileText } from "lucide-react";
import { api, getApiBaseUrl } from "@/lib/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  formatTimeUTC,
  getDecision,
  getDst,
  getEventTime,
  getProto,
  getSrc,
  isAttack,
} from "@/lib/event-utils";

export const Route = createFileRoute("/logs")({
  head: () => ({
    meta: [
      { title: "Logs — Kaavach IDS" },
      { name: "description", content: "Browse, filter and export Kaavach IDS log files." },
    ],
  }),
  component: LogsPage,
});

function LogsPage() {
  const files = useQuery({ queryKey: ["log-files"], queryFn: api.logs });
  const [selected, setSelected] = useState<string>("__today__");
  const [decision, setDecision] = useState<string>("all");
  const [srcFilter, setSrcFilter] = useState("");
  const [reasonFilter, setReasonFilter] = useState("");

  const entries = useQuery({
    queryKey: ["log-entries", selected],
    queryFn: () => (selected === "__today__" ? api.logsToday() : api.logsFile(selected)),
  });

  const filtered = useMemo(() => {
    const all = entries.data ?? [];
    return all.filter((e) => {
      if (decision !== "all") {
        const d = getDecision(e);
        if (decision === "attack" && !isAttack(e)) return false;
        if (decision === "allow" && d !== "ALLOW") return false;
      }
      if (srcFilter && !getSrc(e).includes(srcFilter)) return false;
      if (reasonFilter && !(e.reason ?? "").toLowerCase().includes(reasonFilter.toLowerCase()))
        return false;
      return true;
    });
  }, [entries.data, decision, srcFilter, reasonFilter]);

  const exportHref =
    selected === "__today__"
      ? `${getApiBaseUrl()}/logs/today`
      : api.exportUrl(selected);

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Logs Explorer</h1>
        <p className="text-sm text-muted-foreground">Inspect, filter and export captured events.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Files</CardTitle>
            <CardDescription className="text-xs">
              {files.isLoading ? "Loading…" : `${files.data?.length ?? 0} files`}
            </CardDescription>
          </CardHeader>
          <CardContent className="max-h-[420px] space-y-1 overflow-auto">
            <button
              onClick={() => setSelected("__today__")}
              className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm ${
                selected === "__today__" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Today
            </button>
            {files.data?.map((f) => (
              <button
                key={f.name}
                onClick={() => setSelected(f.name)}
                className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs font-mono ${
                  selected === f.name ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                }`}
              >
                <FileText className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{f.name}</span>
              </button>
            ))}
            {files.isError && (
              <p className="text-xs text-destructive">Could not load file list.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-3 pb-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <CardTitle className="text-base">
                  {selected === "__today__" ? "Today's events" : selected}
                </CardTitle>
                <CardDescription>
                  {entries.isLoading ? "Loading…" : `${filtered.length} of ${entries.data?.length ?? 0} entries`}
                </CardDescription>
              </div>
              <Button asChild size="sm" variant="outline">
                <a href={exportHref} target="_blank" rel="noreferrer" download>
                  <Download className="mr-1.5 h-3.5 w-3.5" /> Export
                </a>
              </Button>
            </div>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <Select value={decision} onValueChange={setDecision}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Decision" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All decisions</SelectItem>
                  <SelectItem value="attack">Attacks only</SelectItem>
                  <SelectItem value="allow">Allowed only</SelectItem>
                </SelectContent>
              </Select>
              <Input
                value={srcFilter}
                onChange={(e) => setSrcFilter(e.target.value)}
                placeholder="Source IP filter"
                className="h-8 font-mono text-xs"
              />
              <Input
                value={reasonFilter}
                onChange={(e) => setReasonFilter(e.target.value)}
                placeholder="Reason contains…"
                className="h-8 text-xs"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-[520px] overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-[10px] uppercase">Time (UTC)</TableHead>
                    <TableHead className="text-[10px] uppercase">Source</TableHead>
                    <TableHead className="text-[10px] uppercase">Destination</TableHead>
                    <TableHead className="text-[10px] uppercase">Proto</TableHead>
                    <TableHead className="text-[10px] uppercase">Decision</TableHead>
                    <TableHead className="text-[10px] uppercase">Reason</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.length === 0 && !entries.isLoading && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-sm text-muted-foreground">
                        No entries.
                      </TableCell>
                    </TableRow>
                  )}
                  {filtered.map((e, i) => {
                    const attack = isAttack(e);
                    return (
                      <TableRow key={i} className={attack ? "bg-destructive/10" : undefined}>
                        <TableCell className="font-mono text-xs">
                          {formatTimeUTC(getEventTime(e))}
                        </TableCell>
                        <TableCell className="font-mono text-xs">{getSrc(e)}</TableCell>
                        <TableCell className="font-mono text-xs">{getDst(e)}</TableCell>
                        <TableCell className="font-mono text-xs uppercase">{getProto(e)}</TableCell>
                        <TableCell>
                          <span
                            className={`inline-flex rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                              attack
                                ? "bg-destructive text-destructive-foreground"
                                : "bg-success/20 text-success"
                            }`}
                          >
                            {getDecision(e)}
                          </span>
                        </TableCell>
                        <TableCell className="max-w-[300px] truncate text-xs text-muted-foreground">
                          {e.reason || "—"}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
