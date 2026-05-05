import { createFileRoute } from "@tanstack/react-router";
import { MonitorControls } from "@/components/MonitorControls";
import { LiveEventsTable } from "@/components/LiveEventsTable";
import { AggregateCards } from "@/components/AggregateCards";
import { ManualPredictForm } from "@/components/ManualPredictForm";
import { ModelHealth } from "@/components/ModelHealth";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, ShieldCheck } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — Kaavach IDS" },
      { name: "description", content: "Live network events, monitor controls and manual predictions." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold tracking-tight">Console Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Real-time intrusion detection and model performance monitoring.
        </p>
      </div>

      <MonitorControls />
      <AggregateCards />

      <Tabs defaultValue="traffic" className="w-full">
        <TabsList className="grid w-full max-w-[400px] grid-cols-2">
          <TabsTrigger value="traffic" className="flex items-center gap-2">
            <Activity className="h-3.5 w-3.5" /> Live Traffic
          </TabsTrigger>
          <TabsTrigger value="model" className="flex items-center gap-2">
            <ShieldCheck className="h-3.5 w-3.5" /> Model Health
          </TabsTrigger>
        </TabsList>
        <div className="mt-4">
          <TabsContent value="traffic" className="m-0">
            <LiveEventsTable />
          </TabsContent>
          <TabsContent value="model" className="m-0">
            <ModelHealth />
          </TabsContent>
        </div>
      </Tabs>

      <ManualPredictForm />
    </div>
  );
}
