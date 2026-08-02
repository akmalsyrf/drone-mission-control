import { apiBase } from "@/lib/config";
import type { Drone, VehicleCommand } from "@/types/telemetry";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const droneApi = {
  list: () => request<Drone[]>("/drones"),
  command: (id: string, command: VehicleCommand, altitude_m?: number) =>
    request<{ status: string }>(`/drones/${id}/commands`, {
      method: "POST",
      body: JSON.stringify({ command, altitude_m }),
    }),
};
