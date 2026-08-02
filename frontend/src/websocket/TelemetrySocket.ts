/**
 * Reconnecting WebSocket client for normalized telemetry.
 * Why separate from TanStack Query: live streams are push-based; Query owns REST.
 */

import type { NormalizedTelemetry } from "@/types/telemetry";

export type TelemetryMessageHandler = (sample: NormalizedTelemetry) => void;

export class TelemetrySocket {
  private socket: WebSocket | NoneSocket = null;
  private closedByUser = false;
  private retryMs = 1000;
  private readonly maxRetryMs = 15000;

  constructor(
    private readonly url: string,
    private readonly onMessage: TelemetryMessageHandler,
    private readonly onStatus?: (connected: boolean) => void,
  ) {}

  connect(): void {
    this.closedByUser = false;
    this.open();
  }

  disconnect(): void {
    this.closedByUser = true;
    this.socket?.close();
    this.socket = null;
  }

  private open(): void {
    const socket = new WebSocket(this.url);
    this.socket = socket;

    socket.onopen = () => {
      this.retryMs = 1000;
      this.onStatus?.(true);
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const sample = JSON.parse(event.data) as NormalizedTelemetry;
        this.onMessage(sample);
      } catch {
        // ignore malformed frames
      }
    };

    socket.onclose = () => {
      this.onStatus?.(false);
      this.socket = null;
      if (!this.closedByUser) {
        window.setTimeout(() => this.open(), this.retryMs);
        this.retryMs = Math.min(this.retryMs * 1.5, this.maxRetryMs);
      }
    };
  }
}

type NoneSocket = null;
