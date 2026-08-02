const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export function apiBase(): string {
  return API_BASE.replace(/\/$/, "");
}

export function wsTelemetryUrl(droneId?: string): string {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const host = import.meta.env.VITE_WS_HOST ?? window.location.host;
  const q = droneId ? `?drone_id=${encodeURIComponent(droneId)}` : "?drone_id=*";
  return `${proto}://${host}/ws/telemetry${q}`;
}
