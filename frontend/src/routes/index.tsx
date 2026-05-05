import { createFileRoute } from "@tanstack/react-router";
import { MonitorControls } from "@/components/MonitorControls";
import { LiveEventsTable } from "@/components/LiveEventsTable";
import { AggregateCards } from "@/components/AggregateCards";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — Kaavach IDS" },
      { name: "description", content: "Live network events, monitor controls and aggregate analytics." },
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
          Real-time intrusion detection and network monitoring.
        </p>
      </div>

      <MonitorControls />
      <AggregateCards />
      
      <div className="space-y-6">
        <LiveEventsTable />
      </div>
    </div>
  );
}
