import { useEffect, useState } from "react";

import { CommandBar } from "@/components/CommandBar";
import { DroneList } from "@/components/DroneList";
import { TelemetryPanel } from "@/components/TelemetryPanel";
import { useDrones } from "@/hooks/useDrones";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { FleetMap } from "@/map/FleetMap";

export function DashboardPage() {
  const { data: drones = [], isLoading, error } = useDrones();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { byDrone, connected } = useTelemetryStream("*");

  useEffect(() => {
    if (!selectedId && drones.length > 0) {
      setSelectedId(drones[0]!.id);
    }
  }, [drones, selectedId]);

  const selected = drones.find((d) => d.id === selectedId) ?? null;
  const telemetry = selectedId ? (byDrone[selectedId] ?? null) : null;

  return (
    <div className="flex min-h-screen flex-col bg-ink-950">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-signal-cyan">
            Fleet ops
          </p>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-white">
            Drone Mission Control
          </h1>
        </div>
        <div className="flex items-center gap-3 font-mono text-xs text-slate-400">
          <span
            className={`h-2 w-2 rounded-full ${connected ? "bg-signal-green" : "bg-signal-red"}`}
          />
          WS {connected ? "live" : "reconnecting"}
        </div>
      </header>

      <main className="grid flex-1 grid-cols-1 gap-0 lg:grid-cols-[280px_1fr_320px]">
        <aside className="border-r border-white/10 bg-ink-900/40">
          <div className="border-b border-white/10 px-4 py-3 font-mono text-[10px] uppercase tracking-wider text-slate-500">
            Vehicles
          </div>
          {isLoading && (
            <p className="px-4 py-6 font-mono text-sm text-slate-400">Loading…</p>
          )}
          {error && (
            <p className="px-4 py-6 font-mono text-sm text-signal-red">
              {(error as Error).message}
            </p>
          )}
          <DroneList
            drones={drones}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </aside>

        <section className="relative min-h-[420px] bg-ink-900">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(61,214,198,0.08),_transparent_55%)]" />
          <FleetMap telemetryByDrone={byDrone} selectedDroneId={selectedId} />
        </section>

        <aside className="border-l border-white/10 bg-ink-900/50">
          <TelemetryPanel
            telemetry={telemetry}
            droneName={selected?.name}
            adapterType={selected?.adapter_type}
          />
          <CommandBar droneId={selectedId} />
        </aside>
      </main>
    </div>
  );
}
