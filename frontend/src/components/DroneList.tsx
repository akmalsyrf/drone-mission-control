import type { Drone } from "@/types/telemetry";

interface DroneListProps {
  drones: Drone[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function DroneList({ drones, selectedId, onSelect }: DroneListProps) {
  if (drones.length === 0) {
    return (
      <p className="px-4 py-6 font-mono text-sm text-slate-400">
        No drones registered. Backend seeds a simulated vehicle on first start.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-1 p-2">
      {drones.map((drone) => {
        const active = drone.id === selectedId;
        return (
          <li key={drone.id}>
            <button
              type="button"
              onClick={() => onSelect(drone.id)}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left transition ${
                active
                  ? "bg-signal-cyan/15 ring-1 ring-signal-cyan/40"
                  : "hover:bg-white/5"
              }`}
            >
              <span>
                <span className="block font-display text-sm font-medium text-white">
                  {drone.name}
                </span>
                <span className="font-mono text-[11px] text-slate-500">
                  {drone.adapter_type}
                </span>
              </span>
              <StatusDot status={drone.connection_status} />
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function StatusDot({ status }: { status: Drone["connection_status"] }) {
  const color =
    status === "online"
      ? "bg-signal-green"
      : status === "connecting"
        ? "bg-signal-amber"
        : status === "error"
          ? "bg-signal-red"
          : "bg-slate-500";
  return (
    <span className="flex items-center gap-2 font-mono text-[10px] uppercase text-slate-400">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      {status}
    </span>
  );
}
