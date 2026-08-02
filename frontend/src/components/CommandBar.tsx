import { useMutation, useQueryClient } from "@tanstack/react-query";

import { droneApi } from "@/lib/api";
import type { VehicleCommand } from "@/types/telemetry";

const COMMANDS: { id: VehicleCommand; label: string }[] = [
  { id: "arm", label: "Arm" },
  { id: "disarm", label: "Disarm" },
  { id: "takeoff", label: "Takeoff" },
  { id: "hold", label: "Hold" },
  { id: "land", label: "Land" },
  { id: "rtl", label: "RTL" },
];

interface CommandBarProps {
  droneId: string | null;
}

export function CommandBar({ droneId }: CommandBarProps) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: ({ command }: { command: VehicleCommand }) => {
      if (!droneId) throw new Error("No drone selected");
      return droneApi.command(droneId, command, command === "takeoff" ? 10 : undefined);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["drones"] });
    },
  });

  return (
    <div className="flex flex-wrap items-center gap-2 border-t border-white/10 px-4 py-3">
      <span className="mr-2 font-mono text-[10px] uppercase tracking-wider text-slate-500">
        Commands
      </span>
      {COMMANDS.map((cmd) => (
        <button
          key={cmd.id}
          type="button"
          disabled={!droneId || mutation.isPending}
          onClick={() => mutation.mutate({ command: cmd.id })}
          className="rounded-md bg-ink-800 px-3 py-1.5 font-display text-sm text-slate-100 ring-1 ring-white/10 transition hover:bg-ink-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {cmd.label}
        </button>
      ))}
      {mutation.isError && (
        <span className="font-mono text-xs text-signal-red">
          {(mutation.error as Error).message}
        </span>
      )}
    </div>
  );
}
