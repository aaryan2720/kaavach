import { useQuery } from "@tanstack/react-query";
import { Timer, Zap, Cpu, Network } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export function ModelHealth() {
  const { data: status, isLoading } = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
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

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div className="space-y-4">
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
              <Network className="h-4 w-4" /> Packets Processed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-mono font-bold">{processed.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Throughput: {throughput} packets/sec
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Cpu className="h-4 w-4" /> Model Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <span>Confidence Threshold</span>
                <span className="font-mono">{Math.round(threshold * 100)}%</span>
              </div>
              <Progress value={threshold * 100} className="h-1.5" />
            </div>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-md bg-muted p-2">
                <p className="text-muted-foreground">Active Model</p>
                <p className="font-semibold truncate">{modelName}</p>
              </div>
              <div className="rounded-md bg-muted p-2">
                <p className="text-muted-foreground">Interface</p>
                <p className="font-semibold">{String(status?.interface || "Auto")}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-primary/5 border-primary/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" /> Live Inference Info
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs leading-relaxed text-muted-foreground">
              The model is currently monitoring the network using <strong>Scapy</strong>. 
              Each packet is analyzed against your <strong>{modelName}</strong> 
              artifact to detect anomalies in real-time.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
