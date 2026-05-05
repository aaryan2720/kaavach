import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, AlertTriangle, Cpu, Crosshair } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { getEventTime, getSrc, isAttack } from "@/lib/event-utils";
import type { NetworkEvent } from "@/lib/types";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip as RTooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Stats {
  total: number;
  attacks: number;
  topAttackers: { ip: string; count: number }[];
  perMinute: { t: string; count: number }[];
}

function compute(events: NetworkEvent[]): Stats {
  const today = new Date().toISOString().slice(0, 10);
  let total = 0;
  let attacks = 0;
  const ipCounts = new Map<string, number>();
  const perMin = new Map<string, number>();

  for (const e of events) {
    const ts = getEventTime(e);
    if (ts.slice(0, 10) === today) total++;
    if (isAttack(e)) {
      attacks++;
      const ip = getSrc(e);
      ipCounts.set(ip, (ipCounts.get(ip) ?? 0) + 1);
    }
    if (ts) {
      const key = ts.slice(0, 16); // YYYY-MM-DDTHH:MM
      perMin.set(key, (perMin.get(key) ?? 0) + 1);
    }
  }

  const topAttackers = [...ipCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([ip, count]) => ({ ip, count }));

  const perMinute = [...perMin.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-20)
    .map(([t, count]) => ({ t: t.slice(11), count }));

  return { total, attacks, topAttackers, perMinute };
}

export function AggregateCards() {
  const { data: events = [] } = useQuery({
    queryKey: ["events"],
    queryFn: () => api.events(300),
  });
  const { data: status } = useQuery({ queryKey: ["status"], queryFn: api.status });

  const stats = useMemo(() => compute(events), [events]);
  const modelVersion = (status?.model_version as string) || "n/a";

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        icon={<Activity className="h-4 w-4 text-primary" />}
        label="Events Today"
        value={stats.total}
      />
      <StatCard
        icon={<AlertTriangle className="h-4 w-4 text-destructive" />}
        label="Attacks Today"
        value={stats.attacks}
        tone="danger"
      />
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Crosshair className="h-4 w-4 text-warning" /> Top Attackers
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {stats.topAttackers.length === 0 ? (
            <p className="text-sm text-muted-foreground">None detected</p>
          ) : (
            <ul className="space-y-1 text-xs">
              {stats.topAttackers.map((a) => (
                <li key={a.ip} className="flex justify-between font-mono">
                  <span className="truncate">{a.ip}</span>
                  <span className="text-destructive">{a.count}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            <Cpu className="h-4 w-4 text-primary" /> Model Version
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="font-mono text-lg font-semibold">{modelVersion}</div>
          <p className="text-xs text-muted-foreground">
            {status?.running ? "Inference active" : "Idle"}
          </p>
        </CardContent>
      </Card>

      <Card className="col-span-1 sm:col-span-2 lg:col-span-4">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Events / minute</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="h-40 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.perMinute}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.78 0.16 195)" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="oklch(0.78 0.16 195)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="t"
                  stroke="oklch(0.7 0.02 250)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  stroke="oklch(0.7 0.02 250)"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  width={28}
                />
                <RTooltip
                  contentStyle={{
                    background: "oklch(0.22 0.025 250)",
                    border: "1px solid oklch(0.3 0.025 250)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="oklch(0.78 0.16 195)"
                  strokeWidth={2}
                  fill="url(#g1)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  tone?: "danger";
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          {icon} {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div
          className={`font-mono text-2xl font-semibold ${
            tone === "danger" ? "text-destructive" : ""
          }`}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  );
}
