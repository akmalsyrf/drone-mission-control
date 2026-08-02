import { useEffect, useRef } from "react";
import maplibregl, { type Map as MapLibreMap, type Marker } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import type { NormalizedTelemetry } from "@/types/telemetry";

const DEFAULT_CENTER: [number, number] = [8.545594, 47.397742];
const MAX_PATH_POINTS = 200;

interface FleetMapProps {
  telemetryByDrone: Record<string, NormalizedTelemetry>;
  selectedDroneId?: string | null;
}

/**
 * MapLibre fleet map: marker + heading + trailing flight path.
 */
export function FleetMap({ telemetryByDrone, selectedDroneId }: FleetMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markersRef = useRef<Map<string, Marker>>(new Map());
  const pathsRef = useRef<Map<string, [number, number][]>>(new Map());

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: DEFAULT_CENTER,
      zoom: 14,
    });
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");

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
          "line-color": "#3dd6c6",
          "line-width": 2.5,
          "line-opacity": 0.85,
        },
      });
    });

    mapRef.current = map;
    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current.clear();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const activeIds = new Set(Object.keys(telemetryByDrone));
    for (const [id, marker] of markersRef.current) {
      if (!activeIds.has(id)) {
        marker.remove();
        markersRef.current.delete(id);
        pathsRef.current.delete(id);
      }
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

      const el =
        (markersRef.current.get(id)?.getElement() as HTMLDivElement | undefined) ??
        document.createElement("div");
      el.className = "drone-marker";
      el.style.width = "0";
      el.style.height = "0";
      el.style.borderLeft = "7px solid transparent";
      el.style.borderRight = "7px solid transparent";
      el.style.borderBottom = `16px solid ${
        id === selectedDroneId ? "#3dd6c6" : sample.armed ? "#f0b429" : "#3ecf8e"
      }`;
      el.style.transform = `rotate(${sample.heading_deg ?? 0}deg)`;
      el.style.filter = "drop-shadow(0 0 4px rgba(61,214,198,0.45))";

      let marker = markersRef.current.get(id);
      if (!marker) {
        marker = new maplibregl.Marker({ element: el, rotationAlignment: "map" })
          .setLngLat([lon, lat])
          .addTo(map);
        markersRef.current.set(id, marker);
      } else {
        marker.setLngLat([lon, lat]);
      }

      if (!selectedDroneId || id === selectedDroneId) {
        focus = [lon, lat];
      }
    }

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

    if (focus) {
      map.easeTo({ center: focus, duration: 400 });
    }
  }, [telemetryByDrone, selectedDroneId]);

  return <div ref={containerRef} className="h-full w-full" />;
}
