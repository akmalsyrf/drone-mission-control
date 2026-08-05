import type { Map as MapLibreMap } from "maplibre-gl";

import {
  CUSTOM_OVERLAY_LAYER_ID,
  CUSTOM_OVERLAY_SOURCE_ID,
  type CustomMapOverlaySpec,
} from "./mapDefaults";

/**
 * Future DEMNAS / GeoTIFF upload: register a raster overlay on top of the basemap.
 * Call from an upload UI once backend serves tiles or a blob URL.
 */
export function applyCustomMapOverlay(map: MapLibreMap, overlay: CustomMapOverlaySpec): void {
  if (map.getLayer(CUSTOM_OVERLAY_LAYER_ID)) {
    map.removeLayer(CUSTOM_OVERLAY_LAYER_ID);
  }
  if (map.getSource(CUSTOM_OVERLAY_SOURCE_ID)) {
    map.removeSource(CUSTOM_OVERLAY_SOURCE_ID);
  }

  map.addSource(CUSTOM_OVERLAY_SOURCE_ID, {
    type: "image",
    url: overlay.url,
    coordinates: overlay.bounds ?? defaultBaylandsBounds(),
  });

  map.addLayer({
    id: CUSTOM_OVERLAY_LAYER_ID,
    type: "raster",
    source: CUSTOM_OVERLAY_SOURCE_ID,
    paint: {
      "raster-opacity": overlay.opacity ?? 0.75,
    },
  });
}

export function clearCustomMapOverlay(map: MapLibreMap): void {
  if (map.getLayer(CUSTOM_OVERLAY_LAYER_ID)) {
    map.removeLayer(CUSTOM_OVERLAY_LAYER_ID);
  }
  if (map.getSource(CUSTOM_OVERLAY_SOURCE_ID)) {
    map.removeSource(CUSTOM_OVERLAY_SOURCE_ID);
  }
}

function defaultBaylandsBounds(): [
  [number, number],
  [number, number],
  [number, number],
  [number, number],
] {
  // Rough placeholder around Baylands park — replace when uploading a georeferenced DEM.
  const cLng = -121.998877;
  const cLat = 37.412176;
  const d = 0.02;
  return [
    [cLng - d, cLat + d],
    [cLng + d, cLat + d],
    [cLng + d, cLat - d],
    [cLng - d, cLat - d],
  ];
}
