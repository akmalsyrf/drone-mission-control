import { useEffect, useState } from "react";

import { wsTelemetryUrl } from "@/lib/config";
import type { NormalizedTelemetry } from "@/types/telemetry";
import { TelemetrySocket } from "@/websocket/TelemetrySocket";

export function useTelemetryStream(droneId?: string): {
  telemetry: NormalizedTelemetry | null;
  byDrone: Record<string, NormalizedTelemetry>;
  connected: boolean;
} {
  const [byDrone, setByDrone] = useState<Record<string, NormalizedTelemetry>>({});
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const socket = new TelemetrySocket(
      wsTelemetryUrl(droneId),
      (sample) => {
        setByDrone((prev) => ({ ...prev, [sample.drone_id]: sample }));
      },
      setConnected,
    );
    socket.connect();
    return () => socket.disconnect();
  }, [droneId]);

  const telemetry =
    droneId && droneId !== "*"
      ? (byDrone[droneId] ?? null)
      : (Object.values(byDrone)[0] ?? null);

  return { telemetry, byDrone, connected };
}
