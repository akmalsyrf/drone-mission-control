/**
 * Drone visual catalog for the fleet map.
 *
 * Research note (no free "pick a DJI model" catalog API):
 * - Sketchfab Download API can list/search CC-licensed models (needs API token +
 *   per-model attribution; not a product catalog).
 * - Kenney / Poly Pizza / OpenGameArt: CC0 low-poly packs (manual download).
 * - Manufacturer APIs (DJI, Autel, etc.): none that expose free commercial 3D assets.
 *
 * We ship procedural Three.js meshes (owned by this project) and expose a stable
 * catalog so future GLTF uploads can plug in without changing the map layer.
 */

import type { AdapterType } from "@/types/telemetry";

export type DroneVisualId = "x500" | "iris" | "generic";

export type DroneVisualSource = "procedural" | "gltf";

export interface DroneVisualOption {
  id: DroneVisualId;
  label: string;
  source: DroneVisualSource;
  /** Reserved for user-uploaded / Sketchfab-hosted glTF */
  gltfUrl?: string | null;
  description: string;
}

export const DRONE_VISUAL_OPTIONS: readonly DroneVisualOption[] = [
  {
    id: "x500",
    label: "PX4 X500",
    source: "procedural",
    description: "Compact quadcopter silhouette matching Gazebo x500 SITL",
  },
  {
    id: "iris",
    label: "Iris-style quad",
    source: "procedural",
    description: "Slightly wider arms; classic PX4 iris proportions",
  },
  {
    id: "generic",
    label: "Generic quad",
    source: "procedural",
    description: "Neutral UAV marker for simulated / unknown airframes",
  },
] as const;

export function visualForAdapter(adapter: AdapterType | undefined): DroneVisualId {
  switch (adapter) {
    case "gazebo":
    case "px4":
      return "x500";
    case "dji_cloud":
      return "iris";
    default:
      return "generic";
  }
}
