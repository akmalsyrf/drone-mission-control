import type { NormalizedTelemetry } from "@/types/telemetry";

function fmt(value: number | null | undefined, digits = 1, unit = ""): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}${unit}`;
}

interface TelemetryPanelProps {
  telemetry: NormalizedTelemetry | null;
  droneName?: string;
  adapterType?: string;
}

export function TelemetryPanel({ telemetry, droneName, adapterType }: TelemetryPanelProps) {
  return (
    <section className="flex h-full flex-col gap-4 p-5">
      <header className="border-b border-white/10 pb-3">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-signal-cyan/80">
          Live telemetry
        </p>
        <h2 className="mt-1 font-display text-xl font-semibold text-white">
          {droneName ?? "No drone selected"}
        </h2>
        {adapterType && (
          <p className="mt-1 font-mono text-[11px] text-slate-500">{adapterType}</p>
        )}
      </header>

      {!telemetry ? (
        <p className="font-mono text-sm text-slate-400">Waiting for stream…</p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <Metric
            label="Altitude"
            value={fmt(telemetry.relative_altitude_m ?? telemetry.altitude_m, 1, " m")}
          />
          <Metric label="Speed" value={fmt(telemetry.speed_m_s, 1, " m/s")} />
          <Metric label="Heading" value={fmt(telemetry.heading_deg, 0, "°")} />
          <Metric
            label="Battery"
            value={fmt(telemetry.battery.remaining_percent, 0, "%")}
          />
          <Metric
            label="Latitude"
            value={fmt(telemetry.gps.position?.latitude_deg, 6)}
            mono
          />
          <Metric
            label="Longitude"
            value={fmt(telemetry.gps.position?.longitude_deg, 6)}
            mono
          />
          <Metric label="Mode" value={telemetry.flight_mode} />
          <Metric label="Armed" value={telemetry.armed ? "YES" : "NO"} accent={telemetry.armed} />
        </div>
      )}
    </section>
  );
}

function Metric({
  label,
  value,
  mono,
  accent,
}: {
  label: string;
  value: string;
  mono?: boolean;
  accent?: boolean;
}) {
  return (
    <div className="rounded-lg bg-ink-900/80 px-3 py-2 ring-1 ring-white/5">
      <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500">
        {label}
      </div>
      <div
        className={`mt-1 text-lg font-medium ${mono ? "font-mono" : "font-display"} ${
          accent ? "text-signal-amber" : "text-slate-100"
        }`}
      >
        {value}
      </div>
    </div>
  );
}
