import { createFileRoute } from "@tanstack/react-router";
import { MonitorControls } from "@/components/MonitorControls";
import { LiveEventsTable } from "@/components/LiveEventsTable";
import { AggregateCards } from "@/components/AggregateCards";
import { ManualPredictForm } from "@/components/ManualPredictForm";

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
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Press <kbd className="rounded border border-border bg-muted px-1 font-mono text-[10px]">R</kbd> to refresh,{" "}
          <kbd className="rounded border border-border bg-muted px-1 font-mono text-[10px]">S</kbd> to toggle monitor.
        </p>
      </div>
      <MonitorControls />
      <AggregateCards />
      <LiveEventsTable />
      <ManualPredictForm />
    </div>
  );
}
