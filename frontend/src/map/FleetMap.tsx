import { useEffect, useRef } from "react";
import maplibregl, { type Map as MapLibreMap, type Marker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { DroneFleetLayer, telemetryToPoses } from "./DroneFleetLayer";
import {
  BAYLANDS_CENTER,
  DEFAULT_MAP_BEARING,
  DEFAULT_MAP_MAX_PITCH,
  DEFAULT_MAP_PITCH,
  DEFAULT_MAP_ZOOM,
  createSatelliteBasemapStyle,
} from "./mapDefaults";
import type { NormalizedTelemetry } from "@/types/telemetry";

const MAX_PATH_POINTS = 200;

interface FleetMapProps {
  telemetryByDrone: Record<string, NormalizedTelemetry>;
  selectedDroneId?: string | null;
}

/**
 * Satellite basemap @ Baylands + 3D drone meshes (with 2D pin fallback).
 * Custom DEM overlay: `applyCustomMapOverlay` (future DEMNAS upload).
 */
export function FleetMap({ telemetryByDrone, selectedDroneId }: FleetMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const layerRef = useRef<DroneFleetLayer | null>(null);
  const markersRef = useRef<Map<string, Marker>>(new Map());
  const pathsRef = useRef<Map<string, [number, number][]>>(new Map());
  const followedRef = useRef(false);
  const mapReadyRef = useRef(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: createSatelliteBasemapStyle(),
      center: BAYLANDS_CENTER,
      zoom: DEFAULT_MAP_ZOOM,
      pitch: DEFAULT_MAP_PITCH,
      bearing: DEFAULT_MAP_BEARING,
      maxPitch: DEFAULT_MAP_MAX_PITCH,
      antialias: true,
    });
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");

    const fleetLayer = new DroneFleetLayer(BAYLANDS_CENTER);
    layerRef.current = fleetLayer;

    map.on("load", () => {
      map.addSource("flight-paths", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "flight-paths-line",
        type: "line",
        source: "flight-paths",
        paint: {
          "line-color": "#5eead4",
          "line-width": 3,
          "line-opacity": 0.9,
        },
      });
      map.addLayer(fleetLayer);
      mapReadyRef.current = true;
    });

    mapRef.current = map;
    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current.clear();
      layerRef.current = null;
      pathsRef.current.clear();
      mapReadyRef.current = false;
      map.remove();
      mapRef.current = null;
      followedRef.current = false;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;

    const activeIds = new Set(Object.keys(telemetryByDrone));
    for (const id of [...markersRef.current.keys()]) {
      if (!activeIds.has(id)) {
        markersRef.current.get(id)?.remove();
        markersRef.current.delete(id);
      }
    }
    for (const id of pathsRef.current.keys()) {
      if (!activeIds.has(id)) pathsRef.current.delete(id);
    }

    let focus: [number, number] | null = null;

    for (const [id, sample] of Object.entries(telemetryByDrone)) {
      const lat = sample.gps.position?.latitude_deg ?? null;
      const lon = sample.gps.position?.longitude_deg ?? null;
      if (lat == null || lon == null) continue;

      const path = pathsRef.current.get(id) ?? [];
      const next: [number, number] = [lon, lat];
      const last = path[path.length - 1];
      if (!last || last[0] !== next[0] || last[1] !== next[1]) {
        path.push(next);
        if (path.length > MAX_PATH_POINTS) path.shift();
        pathsRef.current.set(id, path);
      }

      // Small dark pin as backup (3D mesh is primary)
      upsertPinMarker(
        map,
        markersRef.current,
        id,
        lon,
        lat,
        sample.heading_deg ?? 0,
        id === selectedDroneId,
        sample.armed,
      );

      if (!selectedDroneId || id === selectedDroneId) {
        focus = [lon, lat];
      }
    }

    layer.sync(telemetryToPoses(telemetryByDrone, selectedDroneId));

    if (mapReadyRef.current) {
      const source = map.getSource("flight-paths") as maplibregl.GeoJSONSource | undefined;
      if (source) {
        source.setData({
          type: "FeatureCollection",
          features: [...pathsRef.current.entries()].map(([id, coordinates]) => ({
            type: "Feature",
            properties: { id },
            geometry: { type: "LineString", coordinates },
          })),
        });
      }
    }

    if (focus) {
      const cam = map.getCenter();
      const dist = Math.hypot(cam.lng - focus[0], cam.lat - focus[1]);
      if (!followedRef.current || dist > 0.0015) {
        map.easeTo({
          center: focus,
          zoom: Math.max(map.getZoom(), DEFAULT_MAP_ZOOM),
          pitch: DEFAULT_MAP_PITCH,
          bearing: DEFAULT_MAP_BEARING,
          duration: followedRef.current ? 500 : 800,
        });
        followedRef.current = true;
      }
    }
  }, [telemetryByDrone, selectedDroneId]);

  return <div ref={containerRef} className="h-full w-full" />;
}

function upsertPinMarker(
  map: MapLibreMap,
  store: Map<string, Marker>,
  id: string,
  lon: number,
  lat: number,
  headingDeg: number,
  selected: boolean,
  armed: boolean,
): void {
  let marker = store.get(id);
  const tip = armed ? "#f97316" : "#e2e8f0";
  if (!marker) {
    const el = document.createElement("div");
    el.className = "drone-map-pin";
    el.innerHTML = quadPinSvg(tip, selected);
    el.style.width = "18px";
    el.style.height = "18px";
    el.style.transform = `rotate(${headingDeg}deg)`;
    el.style.filter = "drop-shadow(0 1px 3px rgba(0,0,0,0.75))";
    el.style.opacity = "0.9";
    marker = new maplibregl.Marker({ element: el, rotationAlignment: "map", anchor: "center" })
      .setLngLat([lon, lat])
      .addTo(map);
    store.set(id, marker);
  } else {
    const el = marker.getElement();
    el.innerHTML = quadPinSvg(tip, selected);
    el.style.transform = `rotate(${headingDeg}deg)`;
    marker.setLngLat([lon, lat]);
  }
}

function quadPinSvg(tip: string, selected: boolean): string {
  const ring = selected ? `<circle cx="32" cy="32" r="28" fill="none" stroke="#5eead4" stroke-width="3" opacity="0.9"/>` : "";
  return `<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  ${ring}
  <circle cx="32" cy="32" r="5" fill="#18181b"/>
  <rect x="10" y="30" width="16" height="4" rx="1" fill="#27272a"/>
  <rect x="38" y="30" width="16" height="4" rx="1" fill="#27272a"/>
  <rect x="30" y="10" width="4" height="16" rx="1" fill="#27272a"/>
  <rect x="30" y="38" width="4" height="16" rx="1" fill="#27272a"/>
  <circle cx="14" cy="32" r="3.5" fill="#3f3f46"/>
  <circle cx="50" cy="32" r="3.5" fill="#3f3f46"/>
  <circle cx="32" cy="14" r="3.5" fill="#3f3f46"/>
  <circle cx="32" cy="50" r="3.5" fill="#3f3f46"/>
  <circle cx="40" cy="32" r="2.5" fill="${tip}"/>
</svg>`;
}
