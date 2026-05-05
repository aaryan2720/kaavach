import { useQuery } from "@tanstack/react-query";
import { Timer, Zap, Cpu, Network, BarChart2 } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  ZAxis, 
  Tooltip, 
  ResponsiveContainer,
  Cell,
  CartesianGrid
} from 'recharts';
import { getDecision } from "@/lib/event-utils";

export function ModelHealth() {
  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: 2000,
  });

  const { data: events } = useQuery({
    queryKey: ["events"],
    queryFn: () => api.events(50),
    refetchInterval: 2000,
  });

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
  };

  const uptime = status?.uptime_seconds ?? 0;
  const processed = status?.total_processed ?? 0;
  const throughput = uptime > 0 ? (processed / uptime).toFixed(2) : "0.00";
  const modelName = (status?.model_name as string) || "Kaavach Base v1";
  const threshold = (status?.threshold as number) || 0.5;

  // Prepare scatter data
  const scatterData = (events || []).map(e => {
    const decision = getDecision(e);
    return {
      x: Number(e.rate || 0),
      y: Number(e.sbytes || 0),
      name: decision,
      color: decision === 'CRITICAL' ? '#ef4444' : decision === 'RISK' ? '#f59e0b' : '#22c55e'
    };
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-lg font-semibold tracking-tight">Model Health & Intelligence</h2>
        <p className="text-sm text-muted-foreground">Monitoring the underlying decision engine and performance metrics.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Timer className="h-4 w-4" /> System Uptime
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-mono font-bold">
               {status?.running ? formatUptime(uptime) : "Monitor Offline"}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Network className="h-4 w-4" /> Total Analyzed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-mono font-bold">{processed.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Live Throughput: {throughput} pps
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Cpu className="h-4 w-4" /> Active Model
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-semibold truncate mb-2">{modelName}</div>
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span>Threshold</span>
                <span>{Math.round(threshold * 100)}%</span>
              </div>
              <Progress value={threshold * 100} className="h-1" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <BarChart2 className="h-4 w-4 text-primary" /> Decision Scatter Plot
            </CardTitle>
            <CardDescription className="text-xs">
              Visualizing Rate vs Source Bytes across detection levels.
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  type="number" 
                  dataKey="x" 
                  name="Rate" 
                  unit=" p/s" 
                  fontSize={10} 
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis 
                  type="number" 
                  dataKey="y" 
                  name="Bytes" 
                  unit=" B" 
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                />
                <ZAxis type="number" range={[50, 400]} />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px' }}
                />
                <Scatter name="Decisions" data={scatterData}>
                  {scatterData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-primary/5 border-primary/20 flex flex-col justify-center p-6">
          <div className="space-y-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <Zap className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Inference Intelligence</h3>
              <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                The scatter plot above demonstrates how the model differentiates traffic. 
                <strong> Normal</strong> traffic (Green) typically clusters at low rates and low byte counts. 
                <strong> Risk</strong> (Yellow) and <strong>Critical</strong> (Red) events are often identified 
                by their high packet rates or unusually large data transfers.
              </p>
            </div>
            <div className="pt-4 border-t border-primary/10">
              <div className="flex items-center gap-4 text-xs font-medium">
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-[#22c55e]"></span> Normal</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-[#f59e0b]"></span> Risk</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-[#ef4444]"></span> Critical</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
