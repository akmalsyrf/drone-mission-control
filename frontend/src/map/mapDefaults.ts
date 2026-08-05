/**
 * Shared map defaults for all adapters (sim / gazebo / hardware).
 *
 * GPS home for PX4 `gz_x500` + baylands ≈ Sunnyvale / SF Bay.
 * Basemap: Esri World Imagery (aerial) — closer to Gazebo outdoor look than OSM streets.
 * Future: DEMNAS / GeoTIFF via `applyCustomMapOverlay`.
 */

import type { StyleSpecification } from "maplibre-gl";

/** lng, lat — PX4 Gazebo baylands SITL home */
export const BAYLANDS_CENTER: [number, number] = [-121.998877, 37.412176];

export const DEFAULT_MAP_ZOOM = 18;
export const DEFAULT_MAP_PITCH = 60;
export const DEFAULT_MAP_BEARING = -25;
export const DEFAULT_MAP_MAX_PITCH = 80;

/**
 * Free aerial/satellite raster (no API key). Attribution required.
 * Not a bit-identical Gazebo mesh — closest practical GCS match for “outdoor world”.
 */
export function createSatelliteBasemapStyle(): StyleSpecification {
  return {
    version: 8,
    name: "dmc-satellite",
    sources: {
      "esri-world-imagery": {
        type: "raster",
        tiles: [
          "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        ],
        tileSize: 256,
        attribution:
          'Tiles © <a href="https://www.esri.com/">Esri</a> — Source: Esri, Maxar, Earthstar Geographics',
        maxzoom: 19,
      },
    },
    layers: [
      {
        id: "esri-world-imagery",
        type: "raster",
        source: "esri-world-imagery",
        minzoom: 0,
        maxzoom: 22,
      },
    ],
  };
}

/** @deprecated Prefer createSatelliteBasemapStyle() */
export const DEFAULT_BASEMAP_STYLE =
  "https://tiles.openfreemap.org/styles/liberty";

/**
 * Optional custom overlay registered at runtime (uploaded raster / DEM hillshade).
 * Hook for future DEMNAS / GeoTIFF upload — not wired to a UI yet.
 */
export interface CustomMapOverlaySpec {
  id: string;
  /** MapLibre image/raster source URL or blob URL */
  url: string;
  bounds?: [[number, number], [number, number], [number, number], [number, number]];
  opacity?: number;
}

export const CUSTOM_OVERLAY_SOURCE_ID = "custom-map-overlay";
export const CUSTOM_OVERLAY_LAYER_ID = "custom-map-overlay-raster";
